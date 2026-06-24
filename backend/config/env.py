import os
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL") or ""
supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY") or ""

gemini_api_key = os.getenv("GEMINI_API_KEY") or ""
gemini_model = os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"

jwt_secret = os.getenv("JWT_SECRET") or ""