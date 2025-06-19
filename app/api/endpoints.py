from fastapi import APIRouter
from pydantic import BaseModel
from app.chatbot_modulo.chat_logic import generate_response  # usa tu función real

router = APIRouter()

class ChatInput(BaseModel):
    message: str

@router.post("/chat/")
async def chat_endpoint(input: ChatInput):
    response = generate_response(input.message)
    return {"response": response}

