import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import joblib
import os
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
from supabase import create_client, Client
import seaborn as sns

# Cargar modelo
# BASE_DIR = os.path.dirname(os.path.dirname(__file__))
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

scaler = joblib.load(os.path.join(BASE_DIR, 'app/models/scaler.pkl'))
kmeans = joblib.load(os.path.join(BASE_DIR, 'app/models/kmeans_model.pkl'))

# Título
st.set_page_config(page_title="Dashboard Clustering", layout="wide")
st.title("📊 Dashboard Clustering eCommerce IA")

# Sidebar con menú
menu = st.sidebar.radio("Navegación", ["Dashboard", "Conversaciones por día", "Distribución por Cluster", "Predicción de Cluster"])

# Cargar base de datos
from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, '.env'))

# DB_URL = os.getenv("DATABASE_URL")

supabase_url = os.getenv('SUPABASE_URL')
supabase_apikey=os.getenv('SUPABASE_SERVICE_ROLE_KEY')

def connexion_supabase(url, apikey, tabla):
    cliente_supa= create_client(url, apikey)
    response= ( 
        cliente_supa.table(tabla)
        .select("*")
        .execute()
    )
    data= response.data
    df =pd.DataFrame(data)
    return df

df_logs= connexion_supabase(supabase_url,supabase_apikey,"logs_chat")
df= connexion_supabase(supabase_url,supabase_apikey,"session_summary")
#probar si carga el de logs_chat

# print(DB_URL)
# engine = create_engine(DB_URL)


# @st.cache_data(ttl=600)
# def load_data():
#     try:
#         query = "SELECT * FROM session_summary"
#         with engine.connect() as conn:
#             df = pd.read_sql(query, conn)
#             print("✅ Datos cargados correctamente.")
#             return df
#     except Exception as e:
#         print(f"❌ Error al cargar datos: {e}")
#         return pd.DataFrame()


# df = load_data()

# 📌 Sección 1: KPIs
if menu == "KPIs":
    st.subheader("📌 Indicadores clave")
    st.metric("Total sesiones", len(df))

if menu == "Dashboard":
    st.subheader("📌 Indicadores Clave de Conversaciones")

    # KPIs en fila
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🗂️ Total de sesiones", len(df))
    col2.metric("👥 Usuarios únicos", df["id_usuario"].nunique())
    col3.metric("🕒 Duración promedio (segundos)", round(df["duracion_sesion"].mean(), 2))
    col4.metric("💰 Prob. compra promedio", round(df["probabilidad_compra"].mean(), 2))

    st.markdown("### 📊 Análisis Visual")

    # Distribución de clusters + Media por cluster en una fila
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### Distribución de usuarios por cluster")
        cluster_counts = df["cluster"].value_counts().sort_index()
        fig1, ax1 = plt.subplots()
        cluster_counts.plot(kind="bar", ax=ax1, color="skyblue")
        ax1.set_xlabel("Cluster")
        ax1.set_ylabel("Sesiones")
        st.pyplot(fig1)

    with col_b:
        st.markdown("#### Media de variables por cluster")
        variables = ["mensajes_totales", "duracion_sesion", "interacciones", "probabilidad_compra"]
        mean_by_cluster = df.groupby("cluster")[variables].mean().round(2)
        st.dataframe(mean_by_cluster.style.background_gradient(cmap='Blues'))

    st.markdown("### 📊 Boxplots por Cluster")

    # Organizar boxplots de 2 en 2
    for i in range(0, len(variables), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(variables):
                var = variables[i + j]
                with cols[j]:
                    st.markdown(f"**{var}**")
                    fig, ax = plt.subplots()
                    sns.boxplot(data=df, x="cluster", y=var, ax=ax)
                    ax.set_title(f"{var} por cluster")
                    st.pyplot(fig)

# 📈 Sección 2: Conversaciones por día
elif menu == "Conversaciones por día":
    st.subheader("📈 Conversaciones por día")

    df_v2 = df_logs.copy()
    df_v2["fecha"] = pd.to_datetime(df_v2["fecha"], format='mixed')

    # Sidebar o barra superior: selección de mes y año
    st.markdown("### 📅 Selecciona el mes")
    años_disponibles = df_v2["fecha"].dt.year.unique()
    años_disponibles.sort()

    año = st.selectbox("Año", años_disponibles)
    meses = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
        7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    mes = st.selectbox("Mes", list(meses.keys()), format_func=lambda x: meses[x])

    # Filtrar por mes y año
    df_filtrado = df_v2[(df_v2["fecha"].dt.year == año) & (df_v2["fecha"].dt.month == mes)]

    # Agrupar y graficar
    df_filtrado["solo_fecha"] = df_filtrado["fecha"].dt.date
    conversaciones_por_dia = df_filtrado.groupby("solo_fecha")["id_conversacion"].nunique()

    fig, ax = plt.subplots()
    conversaciones_por_dia.plot(kind="line", ax=ax)
    ax.set_title(f"Conversaciones durante {meses[mes]} {año}")
    ax.set_xlabel("Día")
    ax.set_ylabel("Conversaciones")
    # ax.set_ylim(0, conversaciones_por_dia.max())

    st.pyplot(fig)



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
