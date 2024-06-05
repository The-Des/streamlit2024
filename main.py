import pandas as pd
import numpy as np
from unidecode import unidecode

# Función para extraer la hora de entrada del primer DataFrame
def extract_entry_time(schedule):
    if pd.isnull(schedule):
        return np.nan
    return pd.to_datetime(schedule)

# Leer el primer archivo Excel
df_entry = pd.read_excel('/mnt/data/image.png', sheet_name='Horarios de entrada')

# Eliminar tildes en la columna 'Agente'
df_entry['Agente'] = df_entry['Agente'].apply(unidecode)

# Extraer las horas de entrada
entry_times = df_entry.set_index('Agente').applymap(extract_entry_time)

# Leer el segundo archivo Excel
df_connection = pd.read_excel('/mnt/data/image.png', sheet_name='Total_time_in_state_05272024_1620')

# Filtrar los agentes para excluir a Bryan Roman y Rafael Gonzalez
df_connection = df_connection[~df_connection['Nombre del agente'].isin(['Bryan Roman', 'Rafael Gonzalez'])]

# Filtrar las filas donde el estado es "Online"
df_online = df_connection[df_connection['Estado'] == 'Online']

# Eliminar tildes en la columna 'Nombre del agente'
df_online['Nombre del agente'] = df_online['Nombre del agente'].apply(unidecode)

# Crear una columna combinada de fecha y hora para ordenar correctamente
df_online['Inicio Completo'] = pd.to_datetime(df_online['Hora de inicio del estado - Fecha'].astype(str) + ' ' + df_online['Hora de inicio del estado - Marca de tiempo'].astype(str))

# Ordenar por la columna 'Inicio Completo'
df_online = df_online.sort_values(by='Inicio Completo')

# Agrupar por agente y fecha, y obtener el primer registro de cada día
df_online['Fecha'] = df_online['Hora de inicio del estado - Fecha'].dt.date
df_first_online = df_online.groupby(['Nombre del agente', 'Fecha']).first().reset_index()

# Combinar los DataFrames para obtener las horas de entrada correspondientes
def get_entry_time(row):
    agent = row['Nombre del agente']
    date = pd.to_datetime(row['Fecha'])
    if agent in entry_times.index:
        if date in entry_times.columns:
            return entry_times.at[agent, date]
    return np.nan

df_first_online['Hora de entrada'] = df_first_online.apply(get_entry_time, axis=1)

# Calcular la diferencia de tiempo
df_first_online['Duración'] = df_first_online['Inicio Completo'] - df_first_online['Hora de entrada']

# Crear el nuevo DataFrame con los resultados
df_result = df_first_online[['Nombre del agente', 'Fecha', 'Duración']]

# Mostrar el resultado
print(df_result)
