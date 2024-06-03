import streamlit as st
import pandas as pd
import numpy as np
from unidecode import unidecode

# Cargar el archivo Excel
uploaded_file = st.file_uploader("Sube tu archivo Excel", type=["xlsx"])

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
