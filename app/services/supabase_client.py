from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()  # Carga las variables desde .env

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


# Validación para debug
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ SUPABASE_URL o SUPABASE_KEY no están definidos. Revisa tu .env")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
