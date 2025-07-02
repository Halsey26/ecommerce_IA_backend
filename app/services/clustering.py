# clustering.py
import joblib
import numpy as np
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Cargar una sola vez
scaler = joblib.load(os.path.join(BASE_DIR, 'models', 'scaler.pkl'))
kmeans = joblib.load(os.path.join(BASE_DIR, 'models', 'kmeans_model.pkl'))

def predict_cluster(mensajes_totales, duracion_sesion, interacciones):
    X = np.array([[mensajes_totales, duracion_sesion, interacciones]])
    X_scaled = scaler.transform(X)
    cluster = kmeans.predict(X_scaled)[0]
    return int(cluster)
