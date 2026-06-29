import os
from dotenv import load_dotenv

load_dotenv()
API_BASE: str = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
_TIMEOUT: int = 60