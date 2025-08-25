import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def run_churn(supabase):
    """Modelo de análisis de churn"""
    try:
        data = supabase.table("message_metadata").select(
            "cliente_id, dias_desde_ultima, hizo_compra"
        ).execute()

        df = pd.DataFrame(data.data)
        if df.empty:
            return pd.DataFrame()

        # Regla básica: si no compra hace más de 30 días => riesgo de churn
        df["churn_risk"] = df["dias_desde_ultima"].apply(
            lambda x: "alto" if x and x > 30 else "bajo"
        )

        churn_summary = df.groupby("churn_risk").size().reset_index(name="conteo")
        return churn_summary
        
    except Exception as e:
        print(f"Error en modelo de churn: {e}")
        return pd.DataFrame()

def run_rfm(supabase):
    """Modelo de análisis RFM"""
    try:
        # Traer datos de Supabase
        data = supabase.table("message_metadata").select(
            "cliente_id, valor_compra, dias_desde_ultima, hizo_compra"
        ).execute()

        df = pd.DataFrame(data.data)
        if df.empty:
            return pd.DataFrame(), pd.DataFrame()

        # Calcular Recencia, Frecuencia y Monetario
        rfm = df.groupby("cliente_id").agg(
            recencia=("dias_desde_ultima", "min"),
            frecuencia=("hizo_compra", "sum"),  # Cambiado para contar compras reales
            monetario=("valor_compra", "sum")
        ).reset_index()

        # Segmentación simple
        rfm['R_segment'] = rfm['recencia'].apply(lambda x: 'Reciente' if x <= 30 else 'No reciente')
        rfm['F_segment'] = rfm['frecuencia'].apply(lambda x: 'Frecuente' if x >= 3 else 'No frecuente')
        rfm['M_segment'] = rfm['monetario'].apply(lambda x: 'Alto' if x >= 500 else 'Bajo')

        rfm['RFM_segment'] = rfm['R_segment'] + '-' + rfm['F_segment'] + '-' + rfm['M_segment']

        # Resumen por segmento
        rfm_summary = rfm.groupby('RFM_segment').agg({
            'recencia': 'mean',
            'frecuencia': 'mean',
            'monetario': 'mean',
            'cliente_id': 'count'
        }).rename(columns={'cliente_id': 'cantidad_clientes'}).reset_index()

        return rfm, rfm_summary
        
    except Exception as e:
        print(f"Error en modelo RFM: {e}")
        return pd.DataFrame(), pd.DataFrame()

def run_sentimiento(supabase):
    """Modelo de análisis de sentimiento"""
    try:
        data = supabase.table("message_metadata").select(
            "cliente_id, sentimiento"
        ).execute()

        df = pd.DataFrame(data.data)
        if df.empty:
            return pd.DataFrame()

        # Reemplazar nulos
        df['sentimiento'] = df['sentimiento'].fillna('neutral')

        # Conteo por sentimiento
        sentiment_summary = df.groupby("sentimiento").size().reset_index(name="conteo")

        return sentiment_summary
        
    except Exception as e:
        print(f"Error en modelo de sentimiento: {e}")
        return pd.DataFrame()

def run_recompra(supabase):
    """Modelo de análisis de recompra"""
    try:
        # Traer datos de Supabase
        data = supabase.table("message_metadata").select(
            "cliente_id, hizo_compra, valor_compra"
        ).execute()
        
        df = pd.DataFrame(data.data)
        if df.empty:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        # Número de compras por cliente
        compras = df.groupby("cliente_id")["hizo_compra"].sum().reset_index()
        compras["recompra"] = compras["hizo_compra"].apply(lambda x: 1 if x >= 2 else 0)

        # Probabilidad global de recompra
        prob_recompra = compras["recompra"].mean()
        result = pd.DataFrame([{"probabilidad_recompra": prob_recompra}])

        # Distribución de número de compras
        compras_count = compras.groupby("hizo_compra")["cliente_id"].count().reset_index(name="cantidad_clientes")

        # Cantidad de clientes que recompraron vs no recompraron
        recompra_count = compras.groupby("recompra")["cliente_id"].count().reset_index(name="clientes")
        recompra_count["recompra"] = recompra_count["recompra"].map({0: "No", 1: "Sí"})

        return result, compras_count, recompra_count
        
    except Exception as e:
        print(f"Error en modelo de recompra: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# Diccionario para facilitar el acceso a los modelos
modelos = {
    "churn": run_churn,
    "rfm": run_rfm,
    "sentimiento": run_sentimiento,
    "recompra": run_recompra
}