from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
from app.chatbot_modulo.chat_logic import generate_response

from app.services.supabase_client import supabase


router = APIRouter()

class Message(BaseModel):
    user_id: str
    message: str

# "Base de datos" temporal simulada en memoria (solo durante ejecución)
logs_simulados = []

@router.get("/usuarios/")
def obtener_usuarios():
    response = supabase.table("users").select("*").execute()
    return response.data

@router.post("/chat/")
async def chat_handler(msg: Message):
    response = generate_response(msg.message)

    log = {
        "user_id": msg.user_id,
        "user_input": msg.message,
        "bot_response": response,
        "timestamp": datetime.utcnow().isoformat()
    }

    # Guardamos el log solo en memoria para mostrarlo por UI si se desea
    logs_simulados.append(log)

    return {"response": response, "log": log}

@router.get("/logs/")
def get_logs():
    return {"logs": logs_simulados}

@router.get("/modelo/segmentacion/")
def modelo_segmentacion():
    return {
        "modelo": "kmeans-clientes",
        "estado": "cargado (simulado)",
        "segmentos": ["frecuente", "nuevo", "riesgo_abandono"]
    }

@router.get("/modelo/prediccion/")
def modelo_prediccion():
    return {
        "modelo": "flan-t5-mini",
        "estado": "cargado (simulado)",
        "respuesta": "Este cliente probablemente compre en las próximas 24 horas"
    }


