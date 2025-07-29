from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

def aplicar_clustering(df):
    print("🔍 Aplicando clustering...")
    
    # Seleccionamos las columnas numéricas para el clustering
    columnas_numericas = df.select_dtypes(include=['float64', 'int64']).columns
    X = df[columnas_numericas]

    # Escalamos los datos
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    n_samples = len(df)

    # Número dinámico de clusters: mínimo 2, máximo 5 o la cantidad de filas, lo que sea menor
    if n_samples < 2:
        raise ValueError("❌ No hay suficientes datos para aplicar clustering (mínimo 2 filas).")
    n_clusters = min(5, n_samples)

    print(f"📊 Número de muestras: {n_samples} - Número de clusters usados: {n_clusters}")

    modelo = KMeans(n_clusters=n_clusters, random_state=42)
    df['cluster'] = modelo.fit_predict(X_scaled)

    return df
