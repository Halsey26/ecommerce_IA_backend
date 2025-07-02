
from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
from app.services.supabase_client import supabase
from app.services.chat_logic import obtener_respuesta
import uuid

router = APIRouter()  

class ChatInput(BaseModel):
    user_id: str
    message: str

@router.post("/chat/")
async def chat_endpoint(data: ChatInput):
    id_conversacion = str(uuid.uuid4())

    # Guarda el mensaje del usuario
    supabase.table("logs_chat").insert({
        "id_conversacion": id_conversacion,
        "id_usuario": data.user_id,
        "rol": "user",
        "mensaje": data.message,
        "fecha": datetime.utcnow().isoformat()
    }).execute()

    # Respuesta del bot
    respuesta = obtener_respuesta(data.message)

    # Guarda la respuesta del bot
    supabase.table("logs_chat").insert({
        "id_conversacion": id_conversacion,
        "id_usuario": data.user_id,
        "rol": "bot",
        "mensaje": respuesta,
        "fecha": datetime.utcnow().isoformat()
    }).execute()

    return {"response": respuesta}

try:
    supabase.table("logs_chat").insert({...}).execute()
except Exception as e:
    print("Error al insertar en Supabase:", e)


