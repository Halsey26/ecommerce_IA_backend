from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from app.api.endpoints import router
from app.db import models, database
import os

app = FastAPI()

# CORS para permitir frontend externo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # cámbialo por seguridad luego
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crear las tablas en la DB
models.Base.metadata.create_all(bind=database.engine)

# Templates
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def render_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

app.include_router(router)
