# chatbot_produccion/procesamiento/cargar_datos.py

import pandas as pd
import os

def cargar_json():
    ruta = os.path.join(os.path.dirname(__file__), "..", "Message_v2.json")
    df = pd.read_json(ruta)
    df['createdAt'] = pd.to_datetime(df['createdAt'])
    return df
