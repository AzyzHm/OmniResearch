import os
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL") or ""
supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY") or ""

gemini_api_key = os.getenv("GEMINI_API_KEY") or ""
gemini_model = os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"

jina_api_key = os.getenv("JINA_API_KEY") or ""
tavily_api_key = os.getenv("TAVILY_API_KEY") or ""
exa_api_key = os.getenv("EXA_API_KEY") or ""

jwt_secret = os.getenv("JWT_SECRET") or ""