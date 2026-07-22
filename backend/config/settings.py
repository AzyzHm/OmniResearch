from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings

from backend.config.env import supabase_url, supabase_service_key, jwt_secret, gemini_api_key, gemini_model, jina_api_key, tavily_api_key, exa_api_key, mistral_api_key, mistral_model, force_mistral


class Settings(BaseSettings):
    supabase_url: str = supabase_url
    supabase_service_key: str = supabase_service_key

    jwt_secret: str = jwt_secret
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    cors_origins: str = "http://localhost:8501,http://127.0.0.1:8501,http://localhost:5173,http://127.0.0.1:5173"
    cookie_secure: bool = False

    gemini_api_key: str = gemini_api_key
    gemini_model: str = gemini_model

    chroma_persist_dir: str = "vector_database"

    ui_history_limit: int = 50
    llm_context_limit: int = 10

    embedding_model: str = "embeddinggemma"
    chunk_size: int = 1000
    chunk_overlap: int = 150

    reranker_model_name: str = "BAAI/bge-reranker-base"
    retrieval_pool_size: int = 50
    rerank_top_k: int = 5

    jina_api_key: str = jina_api_key
    tavily_api_key: str = tavily_api_key
    exa_api_key: str = exa_api_key

    mistral_api_key: str = mistral_api_key
    mistral_model: str = mistral_model
    force_mistral: bool = force_mistral.lower() == "true"



    @property
    def cors_origins_list(self) -> List[str]:
        """Parse the comma-separated CORS_ORIGINS string into a clean list."""
        return [o.strip().rstrip("/") for o in self.cors_origins.split(",") if o.strip()]
    


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()