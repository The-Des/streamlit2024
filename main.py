import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title('Reporte de Conectividad de Agentes')

# Cargar horarios desde un archivo de Excel
uploaded_file = st.file_uploader("Carga los horarios desde un archivo Excel", type=["xlsx"])
if uploaded_file:
    # Leer el archivo de Excel
    df = pd.read_excel(uploaded_file, sheet_name=0)
    
    # Verificar si la columna 'Agente' existe
    if 'Agente' not in df.columns:
        st.error("El archivo no contiene la columna 'Agente'. Por favor, verifica el archivo e intenta de nuevo.")
    else:
        st.write("Horarios cargados:")
        st.dataframe(df)
        
        # Transponer el DataFrame para facilitar la manipulación
        df = df.set_index('Agente').T
        
        # Normalizar los datos
        def parse_time_range(time_range):
            if isinstance(time_range, str) and '-' in time_range:
                entrada, salida = time_range.split(' - ')
                return pd.to_datetime(entrada, format='%H:%M').time(), pd.to_datetime(salida, format='%H:%M').time()
            return None, None

        # Convertir los horarios a formato datetime.time
        horario_data = []
        for day in df.columns:
            for agent in df.index:
                entrada, salida = parse_time_range(df.at[agent, day])
                horario_data.append({
                    'Agente': agent,
                    'Día': day,
                    'Entrada': entrada,
                    'Salida': salida
                })
        
        horarios_df = pd.DataFrame(horario_data)
        st.write("Horarios procesados:")
        st.dataframe(horarios_df)

        # Generar gráficos de cumplimiento de horarios
        st.write("Gráficos de cumplimiento de horarios")
        
        # Seleccionar agente y día para visualizar cumplimiento
        agentes = horarios_df['Agente'].unique()
        agente_seleccionado = st.selectbox("Selecciona un agente", agentes)
        
        # Convertir los días al formato adecuado (extraer solo la fecha)
        dias = pd.to_datetime(horarios_df['Día'].unique()).strftime('%d-%b')
        dia_seleccionado = st.selectbox("Selecciona un día", dias)
        
        # Filtrar los datos según selección
        df_filtrado = horarios_df[(horarios_df['Agente'] == agente_seleccionado) & (pd.to_datetime(horarios_df['Día']).dt.strftime('%d-%b') == dia_seleccionado)]
        
        if not df_filtrado.empty and df_filtrado['Entrada'].iloc[0] is not None:
            fig, ax = plt.subplots()
            ax.plot(['Entrada', 'Salida'], [df_filtrado['Entrada'].iloc[0], df_filtrado['Salida'].iloc[0]], marker='o')
            ax.set_title(f'Horario de {agente_seleccionado} en el día {dia_seleccionado}')
            ax.set_xlabel('Tipo')
            ax.set_ylabel('Hora')
            ax.set_ylim([pd.Timestamp('00:00').time(), pd.Timestamp('23:59').time()])
            st.pyplot(fig)
        else:
            st.write("No hay datos para el agente y día seleccionados o el agente tiene descanso/vacaciones.")
