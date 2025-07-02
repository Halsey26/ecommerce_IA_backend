import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import joblib
from supabase import create_client
import os

# 🔽 1. Inicializar cliente Supabase
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(url, key)

# 🔽 2. Leer datos de logs_chat
response = supabase.table("logs_chat").select("*").execute()
df = pd.DataFrame(response.data)

if df.empty:
    raise ValueError("La tabla 'logs_chat' está vacía o no se pudo cargar.")

df['fecha'] = pd.to_datetime(df['fecha'], format='ISO8601', errors='coerce')

if df['fecha'].isna().any():
    print("⚠️ Algunas fechas no se pudieron convertir:")
    print(df[df['fecha'].isna()])


# Muestra los primeros datos
print(df.head())

# Verificar cantidad de conversaciones
print("Total de conversaciones:", df['id_conversacion'].nunique())
print("Conversaciones con 3+ mensajes:", df.groupby('id_conversacion').size().ge(3).sum())

# 🔽 3. Agregación por conversación
agg = df.groupby('id_conversacion').agg({
    'id_usuario': 'first',
    'mensaje': 'count',
    'fecha': ['min', 'max']
}).reset_index()

agg.columns = ['id_conversacion', 'id_usuario', 'mensajes_totales', 'fecha_min', 'fecha_max']

# 🔽 4. Filtrar sesiones con menos de 3 mensajes
agg = agg[agg['mensajes_totales'] >= 3]

# 🔽 Validación para evitar error si no hay datos
if agg.empty:
    print("⚠️ No hay suficientes conversaciones con al menos 3 mensajes. Fin del proceso.")
    exit()

# 🔽 5. Convertir fechas y calcular duración
agg['fecha_min'] = pd.to_datetime(agg['fecha_min'])
agg['fecha_max'] = pd.to_datetime(agg['fecha_max'])
agg['duracion_sesion'] = (agg['fecha_max'] - agg['fecha_min']).dt.total_seconds().fillna(0)
agg['interacciones'] = agg['mensajes_totales']


# 🔽 6. Último mensaje del usuario
ultimos_mensajes = df[df['rol'] == 'user'].sort_values('fecha').groupby('id_conversacion').tail(1)
ultimos_mensajes = ultimos_mensajes[['id_conversacion', 'mensaje']].rename(columns={'mensaje': 'ultimo_mensaje'})
agg = agg.merge(ultimos_mensajes, on='id_conversacion', how='left')


# 🔽 7. Clustering
X = agg[['mensajes_totales', 'duracion_sesion', 'interacciones']]
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

kmeans = KMeans(n_clusters=3, random_state=42)
agg['cluster'] = kmeans.fit_predict(X_scaled)

# 🔽 8. Guardar modelos (ruta absoluta basada en este script)
models_dir = os.path.join(os.path.dirname(__file__), "..", "app", "models")
os.makedirs(models_dir, exist_ok=True)

joblib.dump(scaler, os.path.join(models_dir, "scaler.pkl"))
joblib.dump(kmeans, os.path.join(models_dir, "kmeans_model.pkl"))

# 🔽 9. Insertar en Supabase
for _, row in agg.iterrows():
    data = {
        "id_conversacion": row["id_conversacion"],
        "id_usuario": row["id_usuario"],
        "mensajes_totales": int(row["mensajes_totales"]),
        "duracion_sesion": float(row["duracion_sesion"]),
        "interacciones": int(row["interacciones"]),
        "cluster": int(row["cluster"]),
        "probabilidad_compra": 0.0,  # Placeholder
        "ultimo_mensaje": row["ultimo_mensaje"]
    }

    supabase.table("session_summary").upsert(data, on_conflict=["id_conversacion"]).execute()

print("✅ session_summary actualizada correctamente con último mensaje y sesiones filtradas")
