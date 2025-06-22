from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from app.api import endpoints


app = FastAPI()

# CORS (para permitir Next.js desde otro puerto)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # en producción, reemplaza por origen real
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates
templates = Jinja2Templates(directory="app/templates")

# Ruta: solo el iframe del chatbot
@app.get("/", response_class=HTMLResponse)
async def render_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Ruta: panel completo (chatbot + logs + métricas)
@app.get("/panel", response_class=HTMLResponse)
async def render_panel(request: Request):
    return templates.TemplateResponse("panel.html", {"request": request})

# Incluir todas las rutas del router
app.include_router(endpoints.router)


