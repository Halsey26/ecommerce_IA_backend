import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import joblib
import os
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

# Cargar modelo
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
scaler = joblib.load(os.path.join(BASE_DIR, 'app/models/scaler.pkl'))
kmeans = joblib.load(os.path.join(BASE_DIR, 'app/models/kmeans_model.pkl'))

# Título
st.set_page_config(page_title="Dashboard Clustering", layout="wide")
st.title("📊 Dashboard Clustering eCommerce IA")

# Sidebar con menú
menu = st.sidebar.radio("Navegación", ["KPIs", "Conversaciones por día", "Distribución por Cluster", "Predicción de Cluster"])

# Cargar base de datos
from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, '.env'))

DB_URL = os.getenv("DATABASE_URL")
engine = create_engine(DB_URL)

@st.cache_data(ttl=600)
def load_data():
    query = "SELECT * FROM session_summary"
    return pd.read_sql(query, engine)

df = load_data()

# 📌 Sección 1: KPIs
if menu == "KPIs":
    st.subheader("📌 Indicadores clave")
    st.metric("Total sesiones", len(df))

# 📈 Sección 2: Conversaciones por día
elif menu == "Conversaciones por día":
    if 'fecha' in df.columns:
        st.subheader("📈 Conversaciones por día")
        df_v2 = df.copy()
        df_v2["fecha"] = pd.to_datetime(df_v2["fecha"]).dt.date
        conversaciones_por_dia = df_v2.groupby("fecha")["id_conversacion"].nunique()

        fig, ax = plt.subplots()
        conversaciones_por_dia.plot(kind="line", ax=ax)
        ax.set_title("Conversaciones por día")
        ax.set_xlabel("Fecha")
        ax.set_ylabel("Cantidad de conversaciones")
        st.pyplot(fig)
    else:
        st.warning("No se encontró la columna 'fecha'.")

# 📊 Sección 3: Distribución por cluster
elif menu == "Distribución por Cluster":
    if 'cluster' in df.columns:
        st.subheader("🎯 Distribución por cluster")
        st.bar_chart(df['cluster'].value_counts())

        st.subheader("📈 Estadísticas por cluster")
        st.write(df.groupby('cluster')[['mensajes_totales', 'duracion_sesion', 'interacciones']].describe())
    else:
        st.warning("No se encontró la columna 'cluster'.")

# 🤖 Sección 4: Predicción manual
elif menu == "Predicción de Cluster":
    st.subheader("🤖 Predicción de cluster")
    mensajes_totales = st.number_input("Mensajes totales", min_value=0, value=5)
    duracion_sesion = st.number_input("Duración de la sesión (segundos)", min_value=0, value=60)
    interacciones = st.number_input("Interacciones", min_value=0, value=5)

    if st.button("Predecir cluster"):
        X_input = np.array([[mensajes_totales, duracion_sesion, interacciones]])
        X_scaled = scaler.transform(X_input)
        cluster_pred = kmeans.predict(X_scaled)[0]
        st.success(f"✅ Pertenece al cluster: {cluster_pred}")
