import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title('Reporte de Conectividad de Agentes')

# Cargar horarios desde un archivo de Excel
uploaded_file = st.file_uploader("Carga los horarios desde un archivo Excel", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.write("Horarios cargados:")
    st.dataframe(df)

    # Crear un DataFrame pivote para facilitar la visualización y análisis
    df['Día'] = df['Día'].astype(str)
    pivot_df = df.pivot(index='Día', columns='Agente', values=['Entrada', 'Salida'])
    
    # Visualizar el DataFrame pivote
    st.write("Horarios por agente y día:")
    st.dataframe(pivot_df)

    # Convertir horarios a formato datetime para análisis
    df['Entrada'] = pd.to_datetime(df['Entrada'], format='%H:%M').dt.time
    df['Salida'] = pd.to_datetime(df['Salida'], format='%H:%M').dt.time

    # Generar gráficos de cumplimiento de horarios
    st.write("Gráficos de cumplimiento de horarios")
    
    # Seleccionar agente y día para visualizar cumplimiento
    agentes = df['Agente'].unique()
    agente_seleccionado = st.selectbox("Selecciona un agente", agentes)
    
    dias = df['Día'].unique()
    dia_seleccionado = st.selectbox("Selecciona un día", dias)
    
    # Filtrar los datos según selección
    df_filtrado = df[(df['Agente'] == agente_seleccionado) & (df['Día'] == dia_seleccionado)]
    
    if not df_filtrado.empty:
        fig, ax = plt.subplots()
        ax.plot(df_filtrado['Entrada'], label='Entrada')
        ax.plot(df_filtrado['Salida'], label='Salida')
        ax.set_title(f'Horario de {agente_seleccionado} en el día {dia_seleccionado}')
        ax.set_xlabel('Tiempo')
        ax.set_ylabel('Hora')
        ax.legend()
        st.pyplot(fig)
    else:
        st.write("No hay datos para el agente y día seleccionados.")
