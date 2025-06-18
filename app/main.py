from dotenv import load_dotenv
load_dotenv()

import os
db_url = os.getenv("DATABASE_URL")

from fastapi import FastAPI
from app.api.endpoints import router

app = FastAPI()
app.include_router(router)
