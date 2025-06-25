from fastapi import APIRouter, HTTPException
import logging

# Inicializa logs
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

@router.post("/chat/")
async def chat_endpoint(data: ChatInput):
    id_conversacion = str(uuid.uuid4())

    try:
        supabase.table("logs_chat").insert({
            "id_conversacion": id_conversacion,
            "id_usuario": data.user_id,
            "rol": "user",  # 👈 asegúrate que coincida con el CHECK
            "mensaje": data.message,
            "fecha": datetime.utcnow().isoformat()
        }).execute()
    except Exception as e:
        logger.error(f"Error guardando mensaje del usuario en Supabase: {e}")
        raise HTTPException(status_code=500, detail="Error al guardar mensaje del usuario.")

    try:
        respuesta = obtener_respuesta(data.message)
    except Exception as e:
        logger.error(f"Error generando respuesta del bot: {e}")
        raise HTTPException(status_code=500, detail="Error al generar respuesta del bot.")

    try:
        supabase.table("logs_chat").insert({
            "id_conversacion": id_conversacion,
            "id_usuario": data.user_id,
            "rol": "bot",
            "mensaje": respuesta,
            "fecha": datetime.utcnow().isoformat()
        }).execute()
    except Exception as e:
        logger.error(f"Error guardando respuesta del bot en Supabase: {e}")
        raise HTTPException(status_code=500, detail="Error al guardar respuesta del bot.")

    return {"response": respuesta}
