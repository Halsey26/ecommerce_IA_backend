import os
import uuid
import random
import sys
from datetime import datetime, timedelta
import time

try:
    from supabase import create_client, Client
    import pandas as pd
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Error: {e}")
    print("Instalando dependencias faltantes...")
    os.system(f"{sys.executable} -m pip install supabase pandas python-dotenv")
    from supabase import create_client, Client
    import pandas as pd
    from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Faltan las variables de entorno")
    sys.exit(1)

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Error al conectar con Supabase: {e}")
    sys.exit(1)

# Valores válidos según la estructura de tu tabla
PERFILES_VALIDOS = ['frecuente', 'ocasional', 'indeciso']
SENTIMIENTOS_VALIDOS = ['positivo', 'neutral', 'negativo']

def crear_tabla_mensajes_si_no_existe():
    """
    Crea la tabla de mensajes si no existe
    """
    print("🔍 Verificando existencia de tabla messages...")
    try:
        # Intentar obtener un mensaje para verificar si la tabla existe
        supabase.table("messages").select("id").limit(1).execute()
        print("✅ Tabla messages existe")
        return True
    except Exception as e:
        print(f"❌ Tabla messages no existe: {e}")
        print("📋 Creando tabla messages...")
        
        # Crear la tabla messages
        create_table_query = """
        CREATE TABLE IF NOT EXISTS public.messages (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            "chatId" UUID NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
            parts JSONB NOT NULL,
            attachments JSONB NOT NULL DEFAULT '[]'::JSONB,
            "createdAt" TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_messages_chatId ON public.messages ("chatId");
        CREATE INDEX IF NOT EXISTS idx_messages_createdAt ON public.messages ("createdAt");
        """
        
        try:
            supabase.rpc('exec_sql', {'sql': create_table_query}).execute()
            print("✅ Tabla messages creada exitosamente")
            return True
        except Exception as create_error:
            print(f"❌ Error al crear tabla messages: {create_error}")
            return False

def crear_tabla_metadatos_si_no_existe():
    """
    Crea la tabla de metadatos si no existe
    """
    print("🔍 Verificando existencia de tabla message_metadata...")
    try:
        # Intentar obtener un metadato para verificar si la tabla existe
        supabase.table("message_metadata").select("id").limit(1).execute()
        print("✅ Tabla message_metadata existe")
        return True
    except Exception as e:
        print(f"❌ Tabla message_metadata no existe: {e}")
        print("📋 Creando tabla message_metadata...")
        
        # Crear la tabla message_metadata según tu estructura
        create_table_query = """
        CREATE TABLE IF NOT EXISTS public.message_metadata (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            message_id UUID NOT NULL REFERENCES public.messages(id) ON DELETE CASCADE,
            cliente_id UUID,
            perfil_cliente TEXT CHECK (perfil_cliente IN ('frecuente', 'ocasional', 'indeciso')),
            sentimiento TEXT CHECK (sentimiento IN ('positivo', 'neutral', 'negativo')),
            hizo_compra BOOLEAN,
            valor_compra NUMERIC,
            dias_desde_ultima INTEGER
        );
        
        CREATE INDEX IF NOT EXISTS idx_metadata_cliente_id ON public.message_metadata (cliente_id);
        CREATE INDEX IF NOT EXISTS idx_metadata_perfil ON public.message_metadata (perfil_cliente);
        """
        
        try:
            supabase.rpc('exec_sql', {'sql': create_table_query}).execute()
            print("✅ Tabla message_metadata creada exitosamente")
            return True
        except Exception as create_error:
            print(f"❌ Error al crear tabla message_metadata: {create_error}")
            return False

def generar_mensajes_masivos(num_sesiones=1000, mensajes_por_sesion_min=5, mensajes_por_sesion_max=20):
    """
    Genera mensajes masivos para simular interacciones de chatbot
    """
    print(f"📝 Generando {num_sesiones} sesiones de chat...")
    
    # Lista de posibles mensajes de usuario y asistente
    mensajes_usuario = [
        "Hola, necesito ayuda con un producto",
        "¿Tienen este artículo en stock?",
        "Quisiera hacer una devolución",
        "¿Cuál es el tiempo de entrega?",
        "Necesito información sobre garantías",
        "¿Ofrecen descuentos por cantidad?",
        "Mi pedido no ha llegado todavía",
        "¿Cómo funciona el envío express?",
        "Quisiera hablar con un representante",
        "¿Pueden ayudarme a elegir un producto?",
        "Tengo un problema con mi cuenta",
        "¿Aceptan pagos con criptomonedas?",
        "Necesito factura de mi compra",
        "¿Hacen envíos internacionales?",
        "El producto que recibí está dañado"
    ]
    
    mensajes_asistente = [
        "Hola, claro que sí. ¿En qué puedo ayudarte?",
        "Déjame verificar nuestro inventario...",
        "Para devoluciones necesitamos el número de pedido",
        "El tiempo de entrega standard es de 3-5 días",
        "Nuestros productos tienen garantía de 1 año",
        "Sí, ofrecemos descuentos para pedidos mayores a 10 unidades",
        "Puedo rastrear tu pedido, ¿me das el número?",
        "El envío express llega en 24 horas por un costo adicional",
        "Te conecto con un representante, un momento por favor",
        "Claro, ¿qué tipo de producto estás buscando?",
        "Lamento los inconvenientes, vamos a resolverlo",
        "Por el momento no aceptamos criptomonedas",
        "Puedo generarte la factura, ¿cuál es tu RFC?",
        "Sí, hacemos envíos a todo el mundo",
        "Lamento eso, iniciemos el proceso de reemplazo"
    ]
    
    todos_mensajes = []
    
    for i in range(num_sesiones):
        chat_id = str(uuid.uuid4())
        num_mensajes = random.randint(mensajes_por_sesion_min, mensajes_por_sesion_max)
        timestamp = datetime.now() - timedelta(days=random.randint(1, 90))
        
        for j in range(num_mensajes):
            # Alternar entre usuario y asistente
            role = 'user' if j % 2 == 0 else 'assistant'
            
            if role == 'user':
                text = random.choice(mensajes_usuario)
            else:
                text = random.choice(mensajes_asistente)
            
            mensaje = {
                "id": str(uuid.uuid4()),
                "chatId": chat_id,
                "role": role,
                "parts": {"text": text},
                "attachments": [],
                "createdAt": (timestamp + timedelta(minutes=j*2)).isoformat()
            }
            
            todos_mensajes.append(mensaje)
            
            # Insertar por lotes de 100 para no sobrecargar la API
            if len(todos_mensajes) >= 100:
                insertar_mensajes_lote(todos_mensajes)
                todos_mensajes = []
                time.sleep(0.1)  # Pequeña pausa para no sobrecargar
        
        if i % 100 == 0:
            print(f"✅ Procesadas {i} sesiones de chat")
    
    # Insertar los mensajes restantes
    if todos_mensajes:
        insertar_mensajes_lote(todos_mensajes)
    
    print(f"✅ Generadas {num_sesiones} sesiones con aproximadamente {num_sesiones * (mensajes_por_sesion_min + mensajes_por_sesion_max) / 2} mensajes")

def insertar_mensajes_lote(mensajes):
    """
    Inserta un lote de mensajes en la base de datos
    """
    try:
        supabase.table("messages").insert(mensajes).execute()
    except Exception as e:
        print(f"❌ Error al insertar lote de mensajes: {e}")

def generar_metadatos_masivos():
    """
    Genera metadatos masivos para los mensajes existentes
    """
    print("📊 Generando metadatos para los mensajes...")
    
    # Obtener todos los mensajes
    try:
        response = supabase.table("messages").select("id, chatId, createdAt").execute()
        mensajes = response.data
        print(f"📥 Encontrados {len(mensajes)} mensajes")
    except Exception as e:
        print(f"❌ Error al obtener mensajes: {e}")
        return
    
    # Agrupar mensajes por chatId
    chats = {}
    for mensaje in mensajes:
        chat_id = mensaje["chatId"]
        if chat_id not in chats:
            chats[chat_id] = []
        chats[chat_id].append(mensaje)
    
    # Generar clientes únicos para cada chat
    clientes_por_chat = {}
    for chat_id in chats.keys():
        clientes_por_chat[chat_id] = str(uuid.uuid4())
    
    # Generar metadatos
    metadatos = []
    for chat_id, mensajes_chat in chats.items():
        cliente_id = clientes_por_chat[chat_id]
        
        # Ordenar mensajes por fecha
        mensajes_chat.sort(key=lambda x: x["createdAt"])
        
        # Asignar un perfil de cliente para toda la conversación
        perfil_cliente = random.choices(
            PERFILES_VALIDOS,
            weights=[0.3, 0.4, 0.3],  # Pesos para cada perfil
            k=1
        )[0]
        
        # Determinar si hubo compra (más probable para clientes frecuentes)
        probabilidad_compra = 0.8 if perfil_cliente == 'frecuente' else (
            0.5 if perfil_cliente == 'ocasional' else 0.2
        )
        hizo_compra = random.random() < probabilidad_compra
        
        # Calcular valor de compra si hubo
        valor_compra = 0
        if hizo_compra:
            if perfil_cliente == 'frecuente':
                valor_compra = round(random.uniform(100, 1000), 2)
            elif perfil_cliente == 'ocasional':
                valor_compra = round(random.uniform(50, 500), 2)
            else:
                valor_compra = round(random.uniform(20, 200), 2)
        
        # Para cada mensaje en el chat, generar metadatos
        for mensaje in mensajes_chat:
            # El sentimiento puede variar por mensaje, pero tiende a ser consistente en una conversación
            sentimiento_base = random.choices(
                SENTIMIENTOS_VALIDOS,
                weights=[0.6, 0.3, 0.1],  # Más probabilidad de positivo
                k=1
            )[0]
            
            # Pequeña variación aleatoria en el sentimiento
            if random.random() < 0.2:  # 20% de probabilidad de cambiar
                sentimiento = random.choice(SENTIMIENTOS_VALIDOS)
            else:
                sentimiento = sentimiento_base
            
            dias_desde_ultima = random.randint(1, 90)
            
            metadata = {
                "id": str(uuid.uuid4()),
                "message_id": mensaje["id"],
                "cliente_id": cliente_id,
                "perfil_cliente": perfil_cliente,
                "sentimiento": sentimiento,
                "hizo_compra": hizo_compra,
                "valor_compra": float(valor_compra),
                "dias_desde_ultima": dias_desde_ultima
            }
            
            metadatos.append(metadata)
            
            # Insertar por lotes de 100
            if len(metadatos) >= 100:
                insertar_metadatos_lote(metadatos)
                metadatos = []
                time.sleep(0.1)  # Pequeña pausa para no sobrecargar
    
    # Insertar los metadatos restantes
    if metadatos:
        insertar_metadatos_lote(metadatos)
    
    print(f"✅ Generados metadatos para {len(mensajes)} mensajes")

def insertar_metadatos_lote(metadatos):
    """
    Inserta un lote de metadatos en la base de datos
    """
    try:
        supabase.table("message_metadata").insert(metadatos).execute()
    except Exception as e:
        print(f"❌ Error al insertar lote de metadatos: {e}")

def generar_datos_adicionales():
    """
    Genera datos adicionales para análisis RFM y otros modelos
    """
    print("📈 Generando datos adicionales para análisis...")
    
    # Obtener todos los clientes únicos
    try:
        response = supabase.table("message_metadata").select("cliente_id, perfil_cliente").execute()
        metadatos = response.data
        clientes_unicos = set([m["cliente_id"] for m in metadatos])
        print(f"👥 Encontrados {len(clientes_unicos)} clientes únicos")
    except Exception as e:
        print(f"❌ Error al obtener metadatos: {e}")
        return
    
    # Para cada cliente, generar datos de RFM
    for i, cliente_id in enumerate(clientes_unicos):
        if i % 100 == 0:
            print(f"📊 Procesando cliente {i} de {len(clientes_unicos)}")
        
        # Obtener metadatos del cliente
        metadatos_cliente = [m for m in metadatos if m["cliente_id"] == cliente_id]
        perfil_cliente = metadatos_cliente[0]["perfil_cliente"] if metadatos_cliente else "indeciso"
        
        # Calcular métricas RFM basadas en el perfil
        if perfil_cliente == 'frecuente':
            recencia = random.randint(1, 15)  # Compró recientemente
            frecuencia = random.randint(5, 20)  # Muchas compras
            valor_monetario = random.randint(500, 2000)  # Alto valor
        elif perfil_cliente == 'ocasional':
            recencia = random.randint(16, 45)  # Compró hace un tiempo
            frecuencia = random.randint(2, 6)  # Algunas compras
            valor_monetario = random.randint(100, 800)  # Valor medio
        else:  # indeciso
            recencia = random.randint(46, 90)  # Hace mucho que no compra
            frecuencia = random.randint(1, 3)  # Pocas compras
            valor_monetario = random.randint(20, 200)  # Bajo valor
        
        # Aquí podrías almacenar estas métricas en una tabla adicional
        # Por ahora, solo imprimimos para verificar
        if i % 500 == 0:
            print(f"📋 Cliente {cliente_id}: R={recencia}, F={frecuencia}, M={valor_monetario}")

def generar_reporte_final():
    """
    Genera un reporte final de los datos insertados
    """
    print("\n📊 GENERANDO REPORTE FINAL")
    print("=" * 50)
    
    try:
        # Obtener estadísticas de mensajes
        response = supabase.table("messages").select("id", count="exact").execute()
        total_mensajes = response.count
        print(f"💬 Total mensajes: {total_mensajes}")
        
        # Obtener estadísticas de metadatos
        response = supabase.table("message_metadata").select("id", count="exact").execute()
        total_metadatos = response.count
        print(f"📋 Total metadatos: {total_metadatos}")
        
        # Distribución por perfil de cliente
        response = supabase.table("message_metadata").select("perfil_cliente").execute()
        df = pd.DataFrame(response.data)
        if not df.empty:
            print("\n👥 Distribución por perfil de cliente:")
            dist_perfil = df['perfil_cliente'].value_counts()
            for perfil, count in dist_perfil.items():
                print(f"   {perfil}: {count} ({count/len(df)*100:.1f}%)")
        
        # Distribución por sentimiento
        response = supabase.table("message_metadata").select("sentimiento").execute()
        df = pd.DataFrame(response.data)
        if not df.empty:
            print("\n😊 Distribución por sentimiento:")
            dist_sentimiento = df['sentimiento'].value_counts()
            for sentimiento, count in dist_sentimiento.items():
                print(f"   {sentimiento}: {count} ({count/len(df)*100:.1f}%)")
        
        # Estadísticas de compras
        response = supabase.table("message_metadata").select("hizo_compra, valor_compra").execute()
        df = pd.DataFrame(response.data)
        if not df.empty:
            compras_realizadas = df['hizo_compra'].sum()
            print(f"\n💰 Compras realizadas: {compras_realizadas} ({compras_realizadas/len(df)*100:.1f}%)")
            
            if compras_realizadas > 0:
                valor_total = df[df['hijo_compra'] == True]['valor_compra'].sum()
                valor_promedio = valor_total / compras_realizadas
                print(f"   Valor total: ${valor_total:.2f}")
                print(f"   Valor promedio: ${valor_promedio:.2f}")
        
        # Guardar reporte completo
        response = supabase.table("message_metadata").select("*").execute()
        df = pd.DataFrame(response.data)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reporte_completo_{timestamp}.csv"
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"\n💾 Reporte completo guardado como: {filename}")
        
    except Exception as e:
        print(f"❌ Error generando reporte: {e}")

def main():
    """
    Función principal
    """
    print("🚀 GENERADOR DE DATOS SIMULADOS PARA CHATBOT")
    print("=" * 50)
    
    # Verificar y crear tablas si es necesario
    if not crear_tabla_mensajes_si_no_existe():
        print("❌ No se pudo crear la tabla de mensajes")
        return
    
    if not crear_tabla_metadatos_si_no_existe():
        print("❌ No se pudo crear la tabla de metadatos")
        return
    
    # Generar datos
    generar_mensajes_masivos(num_sesiones=500, mensajes_por_sesion_min=3, mensajes_por_sesion_max=10)
    generar_metadatos_masivos()
    generar_datos_adicionales()
    generar_reporte_final()
    
    print("\n🎉 ¡Generación de datos completada!")
    print("📈 Ahora tienes suficientes datos para aplicar modelos de:")
    print("   - Análisis de sentimiento")
    print("   - Segmentación RFM")
    print("   - Predicción de churn")
    print("   - Análisis de recompra")

if __name__ == "__main__":
    main()