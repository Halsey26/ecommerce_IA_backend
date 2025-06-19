from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.database import SessionLocal
from app.db.models import ChatLog
from app.chatbot_modulo.chat_logic import generate_response

router = APIRouter()

class Message(BaseModel):
    user_id: str
    message: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/chat/")
async def chat_handler(msg: Message, db: Session = Depends(get_db)):
    response = generate_response(msg.message)

    log = ChatLog(
        user_id=msg.user_id,
        user_input=msg.message,
        bot_response=response,
        timestamp=datetime.utcnow()
    )
    db.add(log)
    db.commit()

    return {"response": response}
