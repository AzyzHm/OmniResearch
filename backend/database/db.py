from functools import lru_cache
from supabase import create_client, Client
from backend.config.settings import get_settings


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    """Return a cached Supabase client (service-role key for full access)."""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_key)