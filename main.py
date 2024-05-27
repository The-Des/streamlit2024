import streamlit as st
import pandas as pd
from datetime import datetime

st.title('Reporte de Conectividad de Agentes')

# Función para convertir string a datetime.time
def convert_to_time(time_str):
    try:
        return datetime.strptime(time_str, '%H:%M:%S').time()
    except (ValueError, TypeError):
        return None

# Cargar horarios desde un archivo de Excel
uploaded_file_horarios = st.file_uploader("Carga los horarios desde un archivo Excel", type=["xlsx"])
if uploaded_file_horarios:
    # Leer el archivo de Excel
    horarios_df = pd.read_excel(uploaded_file_horarios, sheet_name=0)
    
    # Transponer el DataFrame para poner los días como columnas y los agentes como filas
    horarios_df = horarios_df.set_index('Agente').transpose()

    # Renombrar las columnas después de la transposición
    horarios_df.columns.name = None
    horarios_df = horarios_df.reset_index()
    horarios_df = horarios_df.rename(columns={'index': 'Día'})

    # Imprimir los nombres de las columnas para verificar
    st.write("Columnas del archivo de horarios después de transponer:", horarios_df.columns.tolist())

    # Normalizar y convertir los horarios de entrada y salida a datetime.time
    for column in horarios_df.columns[1:]:  # Saltamos la columna 'Día'
        horarios_df[column] = horarios_df[column].astype(str).apply(lambda x: x.split('-'))
        horarios_df[column] = horarios_df[column].apply(lambda x: [convert_to_time(y) for y in x])

    # Cargar registros de conectividad desde otro archivo Excel
    uploaded_file_registros = st.file_uploader("Carga los registros de conectividad desde un archivo Excel", type=["xlsx"])
    if uploaded_file_registros:
        # Leer el archivo de Excel
        registros_df = pd.read_excel(uploaded_file_registros, sheet_name=0)

        # Verificar si las columnas necesarias existen
        required_columns = ['Hora de inicio del estado - Fecha', 'Nombre del agente', 'Canal', 'Estado', 
                            'Hora de inicio del estado - Marca de tiempo', 'Hora de finalización del estado - Marca de tiempo', 
                            'Tiempo del agente en el estado/segundos']
        if not all(col in registros_df.columns for col in required_columns):
            st.error("El archivo no contiene las columnas necesarias. Por favor, verifica el archivo e intenta de nuevo.")
        else:
            # Filtrar registros por canal 'Chat' y eliminar filas con 'SUM' en la columna 'Estado'
            registros_df = registros_df[(registros_df['Canal'] == 'Chat') & (registros_df['Estado'].isin(['Online', 'Away']))]

            # Convertir columnas de tiempo a datetime.time
            registros_df['Hora de inicio del estado - Marca de tiempo'] = registros_df['Hora de inicio del estado - Marca de tiempo'].astype(str).apply(convert_to_time)
            registros_df['Hora de finalización del estado - Marca de tiempo'] = registros_df['Hora de finalización del estado - Marca de tiempo'].astype(str).apply(convert_to_time)

            # Comparar registros con horarios para determinar cumplimiento
            cumplimiento_data = []
            for idx, horario_row in horarios_df.iterrows():
                dia = horario_row['Día']
                for agente in horarios_df.columns[1:]:  # Saltamos la columna 'Día'
                    entrada, salida = horario_row[agente]

                    if entrada is None or salida is None:
                        continue  # Saltar si el agente tiene OFF o VAC
                    
                    # Filtrar registros del agente en el día específico
                    registros_agente = registros_df[(registros_df['Nombre del agente'] == agente) & 
                                                    (registros_df['Hora de inicio del estado - Fecha'] == dia)]

                    if registros_agente.empty:
                        cumplimiento_data.append({
                            'Día': dia,
                            'Agente': agente,
                            'Llegada tarde': 'Sí',
                            'Tiempo tarde (segundos)': None,
                            'Salida temprano': 'Sí',
                            'Tiempo temprano (segundos)': None,
                            'Cumple tiempo': 'No',
                            'Tiempo total (segundos)': 0
                        })
                        continue

                    # Obtener la primera entrada y última salida
                    primera_entrada = min(registros_agente[registros_agente['Estado'] == 'Online']['Hora de inicio del estado - Marca de tiempo'], default=None)
                    ultima_salida = max(registros_agente[registros_agente['Estado'] == 'Online']['Hora de finalización del estado - Marca de tiempo'], default=None)

                    # Calcular tiempo total en estado 'Online' y 'Away'
                    tiempo_total_online = registros_agente['Tiempo del agente en el estado/segundos'].sum()

                    # Cálculo de llegada tarde y salida temprana
    
