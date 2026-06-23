from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.config.env import supabase_url, supabase_service_key, jwt_secret


class Settings(BaseSettings):
    supabase_url: str = supabase_url
    supabase_service_key: str = supabase_service_key

    jwt_secret: str = jwt_secret
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    cors_origins: str = "http://localhost:8501,http://127.0.0.1:8501"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse the comma-separated CORS_ORIGINS string into a clean list."""
        return [o.strip().rstrip("/") for o in self.cors_origins.split(",") if o.strip()]
    


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()