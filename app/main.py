from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router as log_router  # o simplemente "router"

app = FastAPI()

# 👇 Aquí configuras CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","https://chat-demo-ecommerce-304nl3ikt-halsey26s-projects.vercel.app/chat"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Hola desde FastAPI!"}

app.include_router(log_router)
