# chatbot_produccion/flujo_completo.py

from procesamiento.cargar_datos import cargar_json
from procesamiento.features_chat import generar_features_basicos
from procesamiento.nlp_extractor import extraer_keywords
from procesamiento.clustering import aplicar_clustering

def main():
    print("🚀 Cargando datos...")
    df = cargar_json()

    print("🔧 Generando features...")
    features_df = generar_features_basicos(df)

    print("💬 Extrayendo palabras clave (TF-IDF)...")
    tfidf_df = extraer_keywords(df)

    print("🔗 Uniendo features y keywords...")
    final_df = features_df.merge(tfidf_df, on='chatId', how='left')

    print("🔄 Aplicando clustering...")
    final_df = aplicar_clustering(final_df)
    print("✅ Número de filas en el DataFrame final:", len(final_df))

    print("\n✅ Clusters generados. Vista previa:")
    print(final_df[['chatId', 'cluster', 'mensajes_totales', 'duracion_sesion']].head())

    final_df.to_csv("chat_sesiones_clusterizadas.csv", index=False)


if __name__ == "__main__":
    main()
