# chatbot_produccion/procesamiento/features_chat.py

import pandas as pd

def generar_features_basicos(df):
    agg = df.groupby('chatId').agg(
        mensajes_totales=('id', 'count'),
        fecha_inicio=('createdAt', 'min'),
        fecha_fin=('createdAt', 'max')
    ).reset_index()

    agg['duracion_sesion'] = (agg['fecha_fin'] - agg['fecha_inicio']).dt.total_seconds()

    por_usuario = df[df['role'] == 'user'].groupby('chatId').size() / df.groupby('chatId').size()
    agg['porcentaje_user'] = agg['chatId'].map(por_usuario).fillna(0)

    ultimos = df[df['role'] == 'user'].sort_values('createdAt').groupby('chatId').tail(1)
    ultimos = ultimos[['chatId', 'parts']].rename(columns={'parts': 'ultimo_mensaje_user'})

    agg = agg.merge(ultimos, on='chatId', how='left')

    return agg
