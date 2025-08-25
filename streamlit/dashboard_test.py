import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from supabase import create_client, Client
from modelos import rfm, churn, sentimiento, recompra

# --- Cargar .env ---
dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=dotenv_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("❌ No se encontraron SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY en el .env")
    st.stop()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Dashboard Ecommerce", layout="wide")
st.title("📊 Dashboard Ecommerce - Modelos de Clientes")

opcion = st.sidebar.radio(
    "Selecciona el análisis:",
    ["RFM", "Churn", "Sentimiento", "Propensión de Recompra"]
)

def plot_df(df, x=None, y=None, kind="bar", title=""):
    st.subheader(title)
    st.write(df.head(10))  # Mostrar solo primeras 10 filas
    if not df.empty:
        fig, ax = plt.subplots()
        if kind=="bar":
            if x and y:
                df.plot.bar(x=x, y=y, ax=ax)
            else:
                df.plot(kind="bar", ax=ax)
        elif kind=="pie":
            df.set_index(x).plot.pie(y=y, autopct="%1.1f%%", ax=ax, legend=False)
        elif kind=="hist":
            df[y].hist(bins=20, ax=ax)
        st.pyplot(fig)

try:
    if opcion=="RFM":
        df_rfm, rfm_summary = rfm.run(supabase)

        st.subheader("Resumen por Segmento RFM")
        st.dataframe(rfm_summary)

        st.subheader("Distribución de Recencia, Frecuencia y Monetario")
        fig, ax = plt.subplots(1,3, figsize=(18,5))
        df_rfm['recencia'].hist(bins=20, ax=ax[0])
        ax[0].set_title('Recencia')
        df_rfm['frecuencia'].hist(bins=20, ax=ax[1])
        ax[1].set_title('Frecuencia')
        df_rfm['monetario'].hist(bins=20, ax=ax[2])
        ax[2].set_title('Monetario')
        st.pyplot(fig)

        st.subheader("Cantidad de clientes por RFM Segment")
        rfm_count = df_rfm.groupby('RFM_segment')['cliente_id'].count().reset_index(name='clientes')
        st.bar_chart(rfm_count.set_index('RFM_segment'))

    elif opcion=="Churn":
        df_churn = churn.run(supabase)
        plot_df(df_churn, x="churn_risk", y="conteo", kind="bar", title="Riesgo de Churn por Cliente")

    elif opcion=="Sentimiento":
        df_sent = sentimiento.run(supabase)
        plot_df(df_sent, x="sentimiento", y="conteo", kind="bar", title="Distribución de Sentimiento de Mensajes")

    if opcion == "Propensión de Recompra":
        result, compras_count, recompra_count = recompra.run(supabase)
        
        if not result.empty:
            st.subheader("Probabilidad de Recompra")
            st.write(f"{result.iloc[0]['probabilidad_recompra']:.2%}")

            st.subheader("Distribución de número de compras por cliente")
            st.bar_chart(compras_count.set_index("hizo_compra"))

            st.subheader("Cantidad de clientes que recompraron vs no recompraron")
            st.bar_chart(recompra_count.set_index("recompra"))

        else:
            st.write("No hay datos de recompra disponibles")


except Exception as e:
    st.error(f"❌ Ocurrió un error al ejecutar el análisis: {e}")
