import streamlit as st
import pandas as pd
import numpy as np
from unidecode import unidecode

# Cargar el archivo Excel
uploaded_file = st.file_uploader("Sube el horario", type=["xlsx"])

if uploaded_file:
    # Leer el archivo Excel
    df = pd.read_excel(uploaded_file)

    # Eliminar tildes en la columna 'Agente'
    df['Agente'] = df['Agente'].apply(unidecode)
    
    # Función para extraer la hora de entrada
    def extract_entry_time(schedule):
        if schedule in ["OFF", "VAC"]:
            return np.nan
        return pd.to_datetime(schedule.split(' - ')[0], format='%H:%M')
    
    # Aplicar la función a todas las columnas excepto la columna 'Agente'
    entry_times = df.set_index('Agente').applymap(extract_entry_time)

    # Guardar el resultado en memoria
    st.session_state['entry_times'] = entry_times

    # Cargar el segundo archivo Excel
    uploaded_file = st.file_uploader("Sube el horario de conexión", type=["xlsx"])

    if uploaded_file:
        # Leer el archivo Excel
        df = pd.read_excel(uploaded_file)

    try:
    
        # Filtrar los agentes para excluir a Bryan Roman y Rafael Gonzalez
        df = df[~df['Nombre del agente'].isin(['Bryan Roman', 'Rafael Gonzalez'])]

        # Filtrar las filas donde el estado es "Online"
        df_online = df[df['Estado'] == 'Online']

        # Eliminar tildes en la columna 'Agente'
        df['Nombre del agente'] = df['Nombre del agente'].apply(unidecode)
        
        # Convertir la columna de fecha a datetime
        df_online['Hora de inicio del estado - Fecha'] = pd.to_datetime(df_online['Hora de inicio del estado - Fecha'], format='%d %b %y')
    
        # Crear una columna combinada de fecha y hora para ordenar correctamente
        df_online['Hora de inicio del estado - Marca de tiempo'] = pd.to_datetime(df_online['Hora de inicio del estado - Marca de tiempo'], format='%H:%M:%S').dt.time
        df_online['Inicio Completo'] = pd.to_datetime(df_online['Hora de inicio del estado - Fecha'].astype(str) + ' ' + df_online['Hora de inicio del estado - Marca de tiempo'].astype(str))
        
        # Ordenar por la columna 'Inicio Completo'
        df_online = df_online.sort_values(by='Inicio Completo')
    
        # Agrupar por agente y fecha, y obtener el primer registro de cada día
        df_online['Fecha'] = df_online['Hora de inicio del estado - Fecha'].dt.date
        df_first_online = df_online.groupby(['Nombre del agente', 'Fecha']).first().reset_index()

        st.write(df_first_online)
    except Exception:
        pass

    # Asegurarnos de que las columnas de fechas en df_first_online son de tipo datetime
    df_first_online['Fecha'] = pd.to_datetime(df_first_online['Fecha'])
    df_first_online['Hora de inicio del estado - Marca de tiempo'] = pd.to_datetime(df_first_online['Hora de inicio del estado - Marca de tiempo'], format='%H:%M:%S')
    df_first_online['Inicio Completo'] = pd.to_datetime(df_first_online['Inicio Completo'])

    # Convertir las entradas de entry_times a datetime
    entry_times.columns = pd.to_datetime(entry_times.columns)

    # Crear una lista para almacenar los resultados
    resultados = []

    # Iterar sobre cada fila de df_first_online
    for index, row in df_first_online.iterrows():
        agente = row['Nombre del agente']
        fecha = row['Fecha']
        hora_inicio_real = row['Inicio Completo']
    
        # Buscar la hora de entrada planeada en entry_times
        try:
            hora_entrada_planeada = entry_times.loc[agente, fecha]
            if pd.notnull(hora_entrada_planeada):
                hora_entrada_planeada = pd.Timestamp(hora_entrada_planeada)
                fecha_hora_entrada_planeada = pd.Timestamp.combine(fecha.date(), hora_entrada_planeada.time())
                # Calcular la diferencia
                diferencia = hora_inicio_real - fecha_hora_entrada_planeada
                # Añadir los resultados a la lista
                if diferencia > pd.Timedelta(0):
                    resultados.append([agente, fecha, diferencia])
            else:
                # Si no hay hora de entrada planeada, añadir NaT
                resultados.append([agente, fecha, pd.NaT])
        except KeyError:
            # Si la fecha no está en entry_times, añadir NaT
            resultados.append([agente, fecha, pd.NaT])
    
    # Crear un DataFrame con los resultados
    df_resultados = pd.DataFrame(resultados, columns=['Nombre del agente', 'Fecha', 'Diferencia'])

    # Eliminar las filas donde la diferencia es NaT
    df_resultados = df_resultados.dropna(subset=['Diferencia'])

    # Convertir la columna 'Diferencia' a una cadena en formato HH:MM:SS
    df_resultados['Diferencia'] = df_resultados['Diferencia'].apply(lambda x: str(x).split(' ')[-1])

    # Formatear la columna de fecha para mostrar solo día/mes/año
    df_resultados['Fecha'] = df_resultados['Fecha'].dt.strftime('%d/%m/%Y')
    
    st.write("Tabla de Tardanzas")
    st.dataframe(df_resultados)
