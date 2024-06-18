import streamlit as st
import pandas as pd
import numpy as np
from unidecode import unidecode
import matplotlib.pyplot as plt
import seaborn as sns

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
        df_online = df[(df['Estado'] == 'Online') & (df['Canal'] == 'Messaging')]

        # Eliminar tildes en la columna 'Nombre del agente'
        df_online['Nombre del agente'] = df_online['Nombre del agente'].apply(unidecode)
        
        # Convertir la columna de fecha a datetime y ordenar
        df_online['Fecha'] = pd.to_datetime(df_online['Hora de inicio del estado - Fecha'], format='%d %b %y')
        df_online['Hora de inicio'] = pd.to_datetime(df_online['Hora de inicio del estado - Marca de tiempo'], format='%H:%M:%S').dt.time
        df_online['Inicio Completo'] = pd.to_datetime(df_online['Fecha'].astype(str) + ' ' + df_online['Hora de inicio'].astype(str))

        # Ordenar por la columna 'Inicio Completo'
        df_online = df_online.sort_values(by='Inicio Completo')
    
        # Agrupar por agente y fecha, y obtener el primer registro de cada día
        df_first_online = df_online.groupby(['Nombre del agente', 'Fecha']).first().reset_index()

    except Exception as e:
        pass

    # Asegurarnos de que las columnas de fechas en df_first_online son de tipo datetime
    df_first_online['Fecha'] = pd.to_datetime(df_first_online['Fecha'])

    # Crear una lista para almacenar los resultados
    resultados = []

    # Convertir entry_times a un diccionario para búsqueda rápida
    entry_times_dict = entry_times.to_dict(orient='index')

    # Iterar sobre cada fila de df_first_online
    for index, row in df_first_online.iterrows():
        agente = row['Nombre del agente']
        fecha = row['Fecha']
        hora_inicio_real = row['Inicio Completo']
    
        # Buscar la hora de entrada planeada en entry_times_dict
        hora_entrada_planeada = entry_times_dict.get(agente, {}).get(fecha)
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

    # Crear un DataFrame con los resultados
    df_resultados = pd.DataFrame(resultados, columns=['Nombre del agente', 'Fecha', 'Diferencia'])

    # Eliminar las filas donde la diferencia es NaT
    df_resultados = df_resultados.dropna(subset=['Diferencia'])

    # Convertir la columna 'Diferencia' a una cadena en formato HH:MM:SS
    df_resultados['Diferencia'] = df_resultados['Diferencia'].apply(lambda x: str(x).split(' ')[-1])

    # Convertir la columna 'Fecha' a datetime asegurando el formato día/mes/año
    df_resultados['Fecha'] = pd.to_datetime(df_resultados['Fecha'], format='%d/%m/%Y', errors='coerce')
    
    # Convertir diferencia a segundos para análisis
    df_resultados['Diferencia_Segundos'] = pd.to_timedelta(df_resultados['Diferencia']).dt.total_seconds()

    # Crear un DataFrame con la suma de tardanza por agente y por mes
    df_resultados['Mes'] = df_resultados['Fecha'].dt.to_period('M')
    df_totales = df_resultados.groupby(['Nombre del agente', 'Mes'])['Diferencia_Segundos'].sum().reset_index()
    df_totales['Diferencia'] = pd.to_timedelta(df_totales['Diferencia_Segundos'], unit='s')

    # Convertir 'Diferencia' al formato horas:minutos:segundos
    df_totales['Diferencia'] = df_totales['Diferencia'].apply(lambda x: str(x).split(' ')[-1])

    agent_sidebar_selectbox= st.sidebar.selectbox(
    "Agente",
    ('Angel', 'Angeles')
    )
    
    st.write("#")
    st.title('Reporte de tardanzas')
    st.write("##")


    #Tabla de resultados por día
    st.write("Tabla de Tardanzas")
    st.dataframe(df_resultados)


    #Tabla de resultados por mes
    st.write("Tabla de Tardanzas por Mes")
    st.dataframe(df_totales)
    

    # Gráfico de barras de tardanzas por agente
    fig, ax = plt.subplots(figsize=(10, 8))
    df_total_agente = df_totales.groupby('Nombre del agente')['Diferencia_Segundos'].sum().sort_values()
    bars = ax.barh(df_total_agente.index, df_total_agente.values)
    ax.set_xlabel('Total Tardanza en Segundos')
    ax.set_ylabel('Nombre del Agente')
    ax.set_title('Tardanzas por Agente')

    # Añadir anotaciones
    for bar in bars:
        width = bar.get_width()
        label_x_pos = width - (width * 0.05)  # Posiciona el texto al final de la barra
        ax.text(label_x_pos, bar.get_y() + bar.get_height()/2,
                f'{width/3600:.2f}h',  # Convierte los segundos a horas y formatea con dos decimales
                va='center', ha='right' if width > 0 else 'left', color='white', fontsize=10)
    
    st.pyplot(fig)


    # Heatmap de tardanzas
    st.write("Heatmap de Tardanzas")
    heatmap_data = df_resultados.pivot_table(index='Nombre del agente', columns='Fecha', values='Diferencia_Segundos', fill_value=0)
    plt.figure(figsize=(15, 8))
    sns.heatmap(heatmap_data, cmap='YlGnBu', linewidths=0.5)
    plt.xlabel('Fecha')
    plt.ylabel('Nombre del Agente')
    st.pyplot(plt)
