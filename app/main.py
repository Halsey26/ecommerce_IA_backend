from app.db.database import init_db
init_db()

from fastapi import FastAPI
from app.api.endpoints import router

app = FastAPI()
app.include_router(router)
