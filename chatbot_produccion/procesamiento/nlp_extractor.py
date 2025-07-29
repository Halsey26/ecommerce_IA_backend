import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

def extraer_keywords(df_original):
    # Aplanar las listas en la columna 'parts', extrayendo los campos 'text'
    df_flat = df_original.copy()
    df_flat['mensaje'] = df_flat['parts'].apply(
        lambda x: " ".join([parte['text'] for parte in x if isinstance(parte, dict) and 'text' in parte])
        if isinstance(x, list) else str(x)
    )

    # Filtrar solo mensajes del usuario
    mensajes_user = df_flat[df_flat['role'] == 'user']

    # Agrupar todos los mensajes por sesión (chatId)
    mensajes_por_chat = mensajes_user.groupby('chatId')['mensaje'].apply(lambda x: " ".join(x))

    # Aplicar TF-IDF
    vectorizer = TfidfVectorizer(max_features=10)
    X = vectorizer.fit_transform(mensajes_por_chat)

    tfidf_df = pd.DataFrame(X.toarray(), columns=vectorizer.get_feature_names_out())
    tfidf_df['chatId'] = mensajes_por_chat.index

    return tfidf_df
