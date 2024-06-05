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
        
    # Mostrar los resultados (opcional, solo para verificación)
    st.write("Horarios de entrada")
    st.dataframe(entry_times)

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
        df['Agente'] = df['Agente'].apply(unidecode)
        
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
        
        # Mostrar el resultado en Streamlit
        st.write(df_first_online)

    except Exception:
        pass
