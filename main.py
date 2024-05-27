import streamlit as st
import pandas as pd

st.title('Reporte de Conectividad de Agentes')

# Cargar horarios desde un archivo de Excel
uploaded_file_horarios = st.file_uploader("Carga los horarios desde un archivo Excel", type=["xlsx"])
if uploaded_file_horarios:
    # Leer el archivo de Excel
    horarios_df = pd.read_excel(uploaded_file_horarios, sheet_name=0)
    
    # Verificar si la columna 'Agente' existe
    if 'Agente' not in horarios_df.columns:
        st.error("El archivo no contiene la columna 'Agente'. Por favor, verifica el archivo e intenta de nuevo.")
    else:
        # Transponer el DataFrame para facilitar la manipulación
        horarios_df = horarios_df.set_index('Agente').T

        # Normalizar los datos
        def parse_time_range(time_range):
            if isinstance(time_range, str) and '-' in time_range:
                entrada, salida = time_range.split(' - ')
                return pd.to_datetime(entrada, format='%H:%M').time(), pd.to_datetime(salida, format='%H:%M').time()
            return None, None

        # Convertir los horarios a formato datetime.time
        horario_data = []
        for day in horarios_df.columns:
            for agent in horarios_df.index:
                entrada, salida = parse_time_range(horarios_df.at[agent, day])
                horario_data.append({
                    'Día': day,
                    'Agente': agent,
                    'Entrada': entrada,
                    'Salida': salida
                })
        
        horarios_df = pd.DataFrame(horario_data)
        
        # Intercambiar nombres de columnas
        horarios_df = horarios_df.rename(columns={'Día': 'Agente', 'Agente': 'Día'})

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

                # Comparar registros con horarios para determinar cumplimiento
                cumplimiento_data = []
                for _, row in horarios_df.iterrows():
                    dia = row['Día']
                    agente = row['Agente']
                    entrada = row['Entrada']
                    salida = row['Salida']
                    
                    if pd.isnull(entrada) or pd.isnull(salida):
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

                    # Manejo de errores de conversión para depurar problemas
                    try:
                        primera_entrada = pd.to_datetime(registros_agente[registros_agente['Estado'] == 'Online']['Hora de inicio del estado - Marca de tiempo'].iloc[0], format='%H:%M:%S').time()
                        ultima_salida = pd.to_datetime(registros_agente[registros_agente['Estado'] == 'Online']['Hora de finalización del estado - Marca de tiempo'].iloc[-1], format='%H:%M:%S').time()
                    except Exception as e:
                        st.error(f"Error de conversión de tiempo para el agente {agente} en el día {dia}: {e}")
                        continue

                    # Calcular tiempo total en estado 'Online' y 'Away'
                    tiempo_total_online = registros_agente['Tiempo del agente en el estado/segundos'].sum()

                    llegada_tarde = primera_entrada > entrada
                    salida_temprana = ultima_salida < salida
                    cumple_tiempo = tiempo_total_online >= (7 * 3600 + 50 * 60)  # 7 horas y 50 minutos en segundos

                    # Calcular tiempo de llegada tarde y salida temprana
                    tiempo_tarde = None
                    if llegada_tarde:
                        tiempo_tarde = (pd.Timestamp.combine(pd.Timestamp.today(), primera_entrada) - 
                                        pd.Timestamp.combine(pd.Timestamp.today(), entrada)).seconds

                    tiempo_temprano = None
                    if salida_temprana:
                        tiempo_temprano = (pd.Timestamp.combine(pd.Timestamp.today(), salida) - 
                                           pd.Timestamp.combine(pd.Timestamp.today(), ultima_salida)).seconds

                    cumplimiento_data.append({
                        'Día': dia,
                        'Agente': agente,
                        'Llegada tarde': 'Sí' if llegada_tarde else 'No',
                        'Tiempo tarde (segundos)': tiempo_tarde,
                        'Salida temprano': 'Sí' if salida_temprana else 'No',
                        'Tiempo temprano (segundos)': tiempo_temprano,
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
