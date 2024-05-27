import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.title('Reporte de Conectividad de Agentes')

# Función para convertir string a datetime.time
def convert_to_time(time_str):
    try:
        return datetime.strptime(time_str, '%H:%M:%S').time()
    except ValueError:
        return None

# Cargar horarios desde un archivo de Excel
uploaded_file_horarios = st.file_uploader("Carga los horarios desde un archivo Excel", type=["xlsx"])
if uploaded_file_horarios:
    # Leer el archivo de Excel
    horarios_df = pd.read_excel(uploaded_file_horarios, sheet_name=0)

    # Verificar si la columna 'Agente' existe
    if 'Agente' not in horarios_df.columns:
        st.error("El archivo no contiene la columna 'Agente'. Por favor, verifica el archivo e intenta de nuevo.")
    else:
        # Convertir las horas de entrada y salida a datetime.time
        horarios_df['Entrada'] = horarios_df['Entrada'].apply(convert_to_time)
        horarios_df['Salida'] = horarios_df['Salida'].apply(convert_to_time)

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
                registros_df['Hora de inicio del estado - Marca de tiempo'] = registros_df['Hora de inicio del estado - Marca de tiempo'].apply(convert_to_time)
                registros_df['Hora de finalización del estado - Marca de tiempo'] = registros_df['Hora de finalización del estado - Marca de tiempo'].apply(convert_to_time)

                # Comparar registros con horarios para determinar cumplimiento
                cumplimiento_data = []
                for idx, horario_row in horarios_df.iterrows():
                    dia = horario_row['Día']
                    agente = horario_row['Agente']
                    entrada = horario_row['Entrada']
                    salida = horario_row['Salida']
                    
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
                    llegada_tarde = (datetime.combine(datetime.today(), primera_entrada) - 
                                     datetime.combine(datetime.today(), entrada)).total_seconds() if primera_entrada and primera_entrada > entrada else 0
                    salida_temprana = (datetime.combine(datetime.today(), salida) - 
                                       datetime.combine(datetime.today(), ultima_salida)).total_seconds() if ultima_salida and ultima_salida < salida else 0
                    
                    cumple_tiempo = tiempo_total_online >= (7 * 3600 + 50 * 60)  # 7 horas y 50 minutos en segundos

                    cumplimiento_data.append({
                        'Día': dia,
                        'Agente': agente,
                        'Llegada tarde': 'Sí' if llegada_tarde > 0 else 'No',
                        'Tiempo tarde (segundos)': llegada_tarde if llegada_tarde > 0 else None,
                        'Salida temprano': 'Sí' if salida_temprana > 0 else 'No',
                        'Tiempo temprano (segundos)': salida_temprana if salida_temprana > 0 else None,
                        'Cumple tiempo': 'Sí' if cumple_tiempo else 'No',
                        'Tiempo total (segundos)': tiempo_total_online
                    })

                cumplimiento_df = pd.DataFrame(cumplimiento_data)
                st.write("Reporte de Cumplimiento:")
                st.dataframe(cumplimiento_df)

                # Guardar el reporte en un archivo Excel
                output = st.file_uploader("Guardar el reporte en un archivo Excel", type="xlsx")
                if output:
                    cumplimiento_df.to_excel(output, index=False)
                    st.success("Reporte guardado correctamente.")
