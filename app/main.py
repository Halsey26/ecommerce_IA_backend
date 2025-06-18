from fastapi import FastAPI
from app.api.endpoints import router as log_router

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hola desde FastAPI!"}

app.include_router(log_router)  # 👈 Esto importa tus endpoints correctamente

