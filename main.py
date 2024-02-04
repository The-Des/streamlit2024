import streamlit as st 
import pandas as pd 
import numpy as np

# Título y descripción
st.title('UPC Data Science 2024')
st.header('Simulador Ventas')

# Control deslizante para la cantidad de ventas
n = st.slider("Cantidad de ventas", 5,100, step=1)

# Generar datos aleatorios para las ventas
ventas_data = pd.DataFrame(np.random.randn(n), columns=['Ventas'])

# Visualización de las ventas en una gráfica de línea
st.subheader("Gráfico de ventas")
st.line_chart(ventas_data)

# Estadísticas básicas sobre las ventas
st.subheader("Estadísticas de ventas")
st.write("Media de ventas:", round(ventas_data['Ventas'].mean(), 2))
st.write("Mediana de ventas:", round(ventas_data['Ventas'].median(), 2))
st.write("Desviación estándar de ventas:", round(ventas_data['Ventas'].std(), 2))

# Agregar un histograma para mostrar la distribución de ventas
st.subheader("Histograma de ventas")
st.hist(ventas_data['Ventas'], bins=20)

# Agregar un gráfico de dispersión para analizar la relación entre dos variables
st.subheader("Gráfico de dispersión")
x_values = np.random.randn(n)
y_values = np.random.randn(n)
st.scatter_chart(pd.DataFrame({'x': x_values, 'y': y_values}))
