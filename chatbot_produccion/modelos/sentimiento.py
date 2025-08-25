import pandas as pd

def run(supabase):
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

    # Análisis por cliente opcional
    sentiment_by_cliente = df.groupby("cliente_id").agg(
        avg_sentimiento=('sentimiento', lambda x: (x.map({'negativo':0,'neutral':1,'positivo':2})).mean()),
        total_messages=('sentimiento', 'count')
    ).reset_index()

  
    return sentiment_summary
