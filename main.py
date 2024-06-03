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
        return pd.to_datetime(schedule.split(' - ')[0], format='%H:%M').time()
    
    # Aplicar la función a todas las columnas excepto la columna 'Agente'
    entry_times = df.set_index('Agente').applymap(extract_entry_time)

    # Convertir los tiempos de entrada a datetime64[ns] para futuras operaciones
    def time_to_datetime64(time_obj):
        if pd.isna(time_obj):
            return np.nan
        return pd.Timestamp.combine(pd.Timestamp.today(), time_obj)

    entry_times_datetime64 = entry_times.applymap(time_to_datetime64)
    
    # Mostrar los resultados (opcional, solo para verificación)
    st.write("Horarios de entrada en formato time:")
    st.dataframe(entry_times)

    # Guardar el resultado en memoria
    st.session_state['entry_times'] = entry_times
