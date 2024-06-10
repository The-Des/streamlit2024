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

    # Formatear la columna de fecha para mostrar solo día/mes/año
    df_resultados['Fecha'] = df_resultados['Fecha'].dt.strftime('%d/%m/%Y')
    
    st.write("Tabla de Tardanzas")
    st.dataframe(df_resultados)

    # Convertir diferencia a segundos para análisis
    df_resultados['Diferencia_Segundos'] = pd.to_timedelta(df_resultados['Diferencia']).dt.total_seconds()
    
    # Histograma de tardanzas
    st.write("Histograma de Tardanzas")
    plt.figure(figsize=(10, 5))
    sns.histplot(df_resultados['Diferencia_Segundos'], kde=True)
    plt.xlabel('Tardanza en Segundos')
    plt.ylabel('Frecuencia')
    st.pyplot(plt)

    # Gráfico de barras de tardanzas por agente
    st.write("Tardanzas por Agente")
    tardanza_por_agente = df_resultados.groupby('Nombre del agente')['Diferencia_Segundos'].sum().sort_values()
    plt.figure(figsize=(10, 5))
    tardanza_por_agente.plot(kind='barh')
    plt.xlabel('Total Tardanza en Segundos')
    plt.ylabel('Nombre del Agente')
    st.pyplot(plt)

    # Línea de tiempo de tardanzas
    st.write("Línea de Tiempo de Tardanzas")
    df_resultados['Fecha'] = pd.to_datetime(df_resultados['Fecha'], format='%d/%m/%Y')
    plt.figure(figsize=(10, 5))
    sns.lineplot(data=df_resultados, x='Fecha', y='Diferencia_Segundos', hue='Nombre del agente')
    plt.xlabel('Fecha')
    plt.ylabel('Tardanza en Segundos')
    st.pyplot(plt)

