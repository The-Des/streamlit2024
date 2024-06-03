import streamlit as st
import pandas as pd
from datetime import datetime

st.title('Reporte de Conectividad de Agentes')

# Función para convertir string a datetime.time
def extract_entry_time(schedule):
    if schedule in ["OFF","VAC"]:
        return np.nan
    return pd.to_datetime(schedule.split(' - ')[0], format='%H:%M').time()

# Cargar horarios desde un archivo de Excel
uploaded_file_horarios = st.file_uploader("Carga los horarios desde un archivo Excel", type=["xlsx"])
if uploaded_file_horarios:
    # Leer el archivo de Excel
    horarios_df = pd.read_excel(uploaded_file_horarios, sheet_name=0)

entry_times = df.set_index('Agente').applymap(extract_entry_time)

st.write("Información",entry_times)
