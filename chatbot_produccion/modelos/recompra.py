import pandas as pd

def run(supabase):
    try:
        # Traer datos de Supabase
        data = supabase.table("message_metadata").select(
            "cliente_id, hizo_compra, valor_compra"
        ).execute()
        
    except Exception as e:
        # Manejo de error de conexión
        print(f"Error al conectar con Supabase: {e}")
        return pd.DataFrame(), pd.DataFrame()
    
    df = pd.DataFrame(data.data)
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    # Número de compras por cliente
    compras = df.groupby("cliente_id")["hizo_compra"].sum().reset_index()
    compras["recompra"] = compras["hizo_compra"].apply(lambda x: 1 if x >= 2 else 0)

    # Probabilidad global de recompra
    prob_recompra = compras["recompra"].mean()
    result = pd.DataFrame([{"probabilidad_recompra": prob_recompra}])

    # --- Gráficos para Streamlit ---
    # Distribución de número de compras
    compras_count = compras.groupby("hizo_compra")["cliente_id"].count().reset_index(name="cantidad_clientes")

    # Cantidad de clientes que recompraron vs no recompraron
    recompra_count = compras.groupby("recompra")["cliente_id"].count().reset_index(name="clientes")
    recompra_count["recompra"] = recompra_count["recompra"].map({0:"No", 1:"Sí"})

   
    return result, compras_count, recompra_count
