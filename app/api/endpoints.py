from fastapi import APIRouter, Request
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class Log(BaseModel):
    user_id: str
    message: str
    timestamp: datetime = datetime.utcnow()

@router.post("/logs/")
async def receive_log(log: Log):
    print(f"📨 Log recibido: {log}")
    # Aquí podrías guardarlo en PostgreSQL más adelante
    return {"status": "ok", "log": log}