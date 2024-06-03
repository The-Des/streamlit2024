import streamlit as st
import pandas as pd
import numpy as np

# Cargar el archivo Excel
uploaded_file = st.file_uploader("Sube tu archivo Excel", type=["xlsx"])

if uploaded_file:
    # Leer el archivo Excel
    df = pd.read_excel(uploaded_file)
    
    # Función para extraer la hora de entrada
    def extract_entry_time(schedule):
        if schedule in ["OFF", "VAC"]:
            return np.nan
        return pd.to_datetime(schedule.split(' - ')[0], format='%H:%M')
    
    # Aplicar la función a todas las columnas excepto la columna 'Agente'
    entry_times = df.set_index('Agente').applymap(extract_entry_time)
    
    # Convertir los horarios de entrada al formato de duración en int64
    entry_times_int64 = entry_times.applymap(lambda x: x.value if pd.notnull(x) else np.nan)
    
    # Guardar el resultado en memoria
    st.session_state['entry_times'] = entry_times_int64
    
    # Mostrar los resultados (opcional, solo para verificación)
    st.write("Horarios de entrada en formato int64:")
    st.dataframe(entry_times_int64)
