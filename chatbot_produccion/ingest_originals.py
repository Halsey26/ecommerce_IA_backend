import os
import json
import uuid
import random
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Cargar .env desde la raíz del proyecto (2 niveles arriba de este archivo)
BASE_DIR = Path(__file__).resolve().parents[1]   # sube 1 nivel si tu .env está en la raíz
DOTENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=DOTENV_PATH)

# Configuración de Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

assert SUPABASE_URL and SUPABASE_KEY, f"❌ Faltan SUPABASE_URL y/o SUPABASE_SERVICE_ROLE_KEY en {DOTENV_PATH}"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Valores válidos según la estructura de tu tabla
PERFILES_VALIDOS = ['frecuente', 'ocasional', 'indeciso']
SENTIMIENTOS_VALIDOS = ['positivo', 'neutral', 'negativo']

def norm_created_at(s: str) -> str:
    # Acepta 'YYYY-MM-DD HH:MM:SS.mmm' o ISO. Deja a Postgres castear a timestamptz.
    if not s:
        return datetime.utcnow().isoformat() + "Z"
    if "T" not in s and " " in s:
        s = s.replace(" ", "T")
    return s  # Postgres lo parsea

def generar_metadatos_para_mensaje(mensaje, cliente_id_por_chat):
    """
    Genera metadatos para un mensaje basado en el chatId y contenido
    """
    chat_id = mensaje["chatId"]
    
    # Usar el mismo cliente_id para todos los mensajes del mismo chat
    if chat_id not in cliente_id_por_chat:
        cliente_id_por_chat[chat_id] = str(uuid.uuid4())
    
    cliente_id = cliente_id_por_chat[chat_id]
    
    # Determinar perfil basado en el contenido del mensaje
    partes_texto = ""
    if isinstance(mensaje.get("parts"), list):
        for parte in mensaje["parts"]:
            if isinstance(parte, dict) and "text" in parte:
                partes_texto += parte["text"] + " "
    elif isinstance(mensaje.get("parts"), dict) and "text" in mensaje["parts"]:
        partes_texto = mensaje["parts"]["text"]
    
    # Análisis simple del contenido para determinar perfil
    texto = partes_texto.lower()
    
    # Palabras clave para determinar perfil
    palabras_frecuente = ["gracias", "excelente", "recomendar", "comprar", "otra vez", "satisfecho"]
    palabras_ocasional = ["precio", "oferta", "descuento", "envío", "cuánto", "cuando"]
    palabras_indeciso = ["quizás", "tal vez", "pensando", "dudando", "no sé", "talvez"]
    
    # Determinar perfil basado en palabras clave
    perfil_cliente = "indeciso"  # Por defecto
    
    if any(palabra in texto for palabra in palabras_frecuente):
        perfil_cliente = "frecuente"
    elif any(palabra in texto for palabra in palabras_ocasional):
        perfil_cliente = "ocasional"
    elif any(palabra in texto for palabra in palabras_indeciso):
        perfil_cliente = "indeciso"
    else:
        # Si no hay palabras clave, asignar aleatoriamente con pesos
        perfil_cliente = random.choices(
            PERFILES_VALIDOS,
            weights=[0.3, 0.4, 0.3],
            k=1
        )[0]
    
    # Determinar sentimiento basado en el contenido
    palabras_positivas = ["gracias", "excelente", "bueno", "genial", "perfecto", "satisfecho", "contento"]
    palabras_negativas = ["problema", "error", "mal", "devolución", "queja", "insatisfecho", "decepción"]
    
    sentimiento = "neutral"  # Por defecto
    
    if any(palabra in texto for palabra in palabras_positivas):
        sentimiento = "positivo"
    elif any(palabra in texto for palabra in palabras_negativas):
        sentimiento = "negativo"
    else:
        # Si no hay palabras clave, asignar aleatoriamente con pesos
        sentimiento = random.choices(
            SENTIMIENTOS_VALIDOS,
            weights=[0.6, 0.3, 0.1],
            k=1
        )[0]
    
    # Determinar si hubo compra (más probable para clientes frecuentes)
    if perfil_cliente == 'frecuente':
        probabilidad_compra = 0.8
        valor_min, valor_max = 100, 1000
    elif perfil_cliente == 'ocasional':
        probabilidad_compra = 0.5
        valor_min, valor_max = 50, 500
    else:
        probabilidad_compra = 0.2
        valor_min, valor_max = 20, 200
    
    hizo_compra = random.random() < probabilidad_compra
    valor_compra = round(random.uniform(valor_min, valor_max), 2) if hizo_compra else 0
    
    # Días desde última interacción (aleatorio entre 1 y 90)
    dias_desde_ultima = random.randint(1, 90)
    
    return {
        "id": str(uuid.uuid4()),
        "message_id": mensaje["id"],
        "cliente_id": cliente_id,
        "perfil_cliente": perfil_cliente,
        "sentimiento": sentimiento,
        "hizo_compra": hizo_compra,
        "valor_compra": float(valor_compra),
        "dias_desde_ultima": dias_desde_ultima
    }

def main():
    # 1) Carga el JSON original
    json_path = "/home/antonio/Escritorio/Eve/PasantiaPerceivo/ecommerce_IA_backend/chatbot_produccion/Message_v2.json"
    
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
            assert isinstance(raw, list), "El JSON debe ser una lista de mensajes"
    except FileNotFoundError:
        print(f"❌ Archivo no encontrado: {json_path}")
        return
    except json.JSONDecodeError:
        print(f"❌ Error al decodificar JSON: {json_path}")
        return

    print(f"📖 Leyendo {len(raw)} mensajes del archivo JSON")

    # 2) Preparar registros para messages
    records = []
    for m in raw:
        # Sólo columnas originales, sin enriquecer nada
        rec = {
            "id": m["id"],
            "chatId": m["chatId"],
            "role": m["role"],
            "parts": m.get("parts", []),
            "attachments": m.get("attachments", []),
            "createdAt": norm_created_at(m.get("createdAt")),
        }
        records.append(rec)

    # 3) UPSERT a messages por id para evitar duplicados
    BATCH = 500
    inserted_messages = 0
    
    for i in range(0, len(records), BATCH):
        batch = records[i:i+BATCH]
        try:
            supabase.table("messages").upsert(batch, on_conflict="id").execute()
            inserted_messages += len(batch)
            print(f"✅ Lote {i//BATCH + 1}: {len(batch)} mensajes insertados/actualizados")
        except Exception as e:
            print(f"❌ Error al insertar lote {i//BATCH + 1}: {e}")

    print(f"✅ Total: {inserted_messages} mensajes insertados/actualizados en public.messages")

    # 4) Generar y insertar metadatos
    print("\n📊 Generando metadatos para los mensajes...")
    
    # Mapeo de chatId a cliente_id (para mantener consistencia)
    cliente_id_por_chat = {}
    metadatos = []
    
    for mensaje in records:
        metadata = generar_metadatos_para_mensaje(mensaje, cliente_id_por_chat)
        metadatos.append(metadata)
    
    # 5) Insertar metadatos en message_metadata
    inserted_metadata = 0
    
    for i in range(0, len(metadatos), BATCH):
        batch = metadatos[i:i+BATCH]
        try:
            supabase.table("message_metadata").upsert(batch, on_conflict="id").execute()
            inserted_metadata += len(batch)
            print(f"✅ Lote {i//BATCH + 1}: {len(batch)} metadatos insertados/actualizados")
        except Exception as e:
            print(f"❌ Error al insertar lote de metadatos {i//BATCH + 1}: {e}")
    
    print(f"✅ Total: {inserted_metadata} metadatos insertados/actualizados en public.message_metadata")
    
    # 6) Generar reporte final
    print("\n📈 REPORTE FINAL")
    print("=" * 40)
    
    try:
        # Obtener estadísticas de mensajes
        response = supabase.table("messages").select("id", count="exact").execute()
        total_mensajes = response.count
        print(f"💬 Total mensajes en BD: {total_mensajes}")
        
        # Obtener estadísticas de metadatos
        response = supabase.table("message_metadata").select("id", count="exact").execute()
        total_metadatos = response.count
        print(f"📋 Total metadatos en BD: {total_metadatos}")
        
        # Distribución por perfil de cliente
        response = supabase.table("message_metadata").select("perfil_cliente").execute()
        if response.data:
            from collections import Counter
            perfiles = Counter([m["perfil_cliente"] for m in response.data])
            print("\n👥 Distribución por perfil de cliente:")
            for perfil, count in perfiles.items():
                print(f"   {perfil}: {count} ({count/total_metadatos*100:.1f}%)")
        
        # Distribución por sentimiento
        response = supabase.table("message_metadata").select("sentimiento").execute()
        if response.data:
            sentimientos = Counter([m["sentimiento"] for m in response.data])
            print("\n😊 Distribución por sentimiento:")
            for sentimiento, count in sentimientos.items():
                print(f"   {sentimiento}: {count} ({count/total_metadatos*100:.1f}%)")
        
        # Estadísticas de compras
        response = supabase.table("message_metadata").select("hizo_compra", "valor_compra").execute()
        if response.data:
            compras = [m for m in response.data if m["hizo_compra"]]
            print(f"\n💰 Compras realizadas: {len(compras)} ({len(compras)/total_metadatos*100:.1f}%)")
            
            if compras:
                valor_total = sum(m["valor_compra"] for m in compras if m["valor_compra"])
                valor_promedio = valor_total / len(compras)
                print(f"   Valor total: ${valor_total:.2f}")
                print(f"   Valor promedio: ${valor_promedio:.2f}")
    
    except Exception as e:
        print(f"❌ Error generando reporte: {e}")

if __name__ == "__main__":
    main()