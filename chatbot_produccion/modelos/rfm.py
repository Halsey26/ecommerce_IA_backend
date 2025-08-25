import pandas as pd

def run(supabase):
    # Traer datos de Supabase
    data = supabase.table("message_metadata").select(
        "cliente_id, valor_compra, dias_desde_ultima"
    ).execute()

    df = pd.DataFrame(data.data)
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    # Calcular Recencia, Frecuencia y Monetario
    rfm = df.groupby("cliente_id").agg(
        recencia=("dias_desde_ultima", "min"),
        frecuencia=("valor_compra", "count"),
        monetario=("valor_compra", "sum")
    ).reset_index()

    # --- Opción 1: Segmentación simple ---
    rfm['R_segment'] = rfm['recencia'].apply(lambda x: 'Reciente' if x <= 30 else 'No reciente')
    rfm['F_segment'] = rfm['frecuencia'].apply(lambda x: 'Frecuente' if x >= 3 else 'No frecuente')
    rfm['M_segment'] = rfm['monetario'].apply(lambda x: 'Alto' if x >= 500 else 'Bajo')

    rfm['RFM_segment'] = rfm['R_segment'] + '-' + rfm['F_segment'] + '-' + rfm['M_segment']

    # --- Resumen por segmento ---
    rfm_summary = rfm.groupby('RFM_segment').agg({
        'recencia':'mean',
        'frecuencia':'mean',
        'monetario':'mean',
        'cliente_id':'count'
    }).rename(columns={'cliente_id':'cantidad_clientes'}).reset_index()

  
    return rfm, rfm_summary
