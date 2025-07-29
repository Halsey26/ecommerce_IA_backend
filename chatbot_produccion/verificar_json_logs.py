import json
import pandas as pd
import os

# Ruta al archivo (ajusta según tu estructura)
ruta_archivo = "Message_v2.json"


# Cargar JSON
with open(ruta_archivo, "r", encoding="utf-8") as f:
    data = json.load(f)

# Mostrar tipo de dato raíz
print("🔍 Tipo de dato raíz:", type(data))

# Si es lista de mensajes
if isinstance(data, list):
    print(f"✅ Total de mensajes: {len(data)}")
    df = pd.DataFrame(data)
    print("\n🧾 Columnas disponibles:", df.columns.tolist())
    print("\n📌 Primeros mensajes:")
    print(df.head(5))
    
# Si es diccionario con una clave principal que contiene mensajes
elif isinstance(data, dict):
    for clave in data:
        print(f"📁 Clave encontrada: '{clave}' | Tipo: {type(data[clave])}")
    
    # Intentar convertir primer nivel a DataFrame si es posible
    if isinstance(list(data.values())[0], list):
        df = pd.DataFrame(list(data.values())[0])
        print(f"✅ Total de mensajes: {len(df)}")
        print("\n🧾 Columnas disponibles:", df.columns.tolist())
        print("\n📌 Primeros mensajes:")
        print(df.head(5))
    else:
        print("⚠️ No se puede convertir directamente a DataFrame.")
else:
    print("⚠️ Estructura de JSON no esperada.")
