import os
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL") or ""
supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY") or ""

jwt_secret = os.getenv("JWT_SECRET") or ""