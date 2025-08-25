import pandas as pd

def run(supabase):
    data = supabase.table("message_metadata").select(
        "cliente_id, dias_desde_ultima, hizo_compra"
    ).execute()

    df = pd.DataFrame(data.data)
    if df.empty:
        return pd.DataFrame()

    # Regla básica: si no compra hace más de 30 días => riesgo de churn
    df["churn_risk"] = df["dias_desde_ultima"].apply(lambda x: "alto" if x and x > 30 else "bajo")

    churn_summary = df.groupby("churn_risk").size().reset_index(name="conteo")

    return churn_summary
