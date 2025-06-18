from fastapi import APIRouter, Request
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class Log(BaseModel):
    user_id: str
    message: str

from typing import Optional

timestamp: Optional[str] = None


@router.post("/logs/")
async def receive_log(log: Log):
    log.timestamp = log.timestamp or datetime.utcnow().isoformat()
    print(f"📨 Log recibido: {log}")
    return {"status": "ok", "log": log}



class ChatRequest(BaseModel):
    message: str

@router.post("/chat/")
async def chat_endpoint(req: ChatRequest):
    user_msg = req.message

    # Aquí va tu lógica IA para procesar user_msg y generar respuesta
    response = f"Echo: {user_msg}"

    return {"response": response}