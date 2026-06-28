from functools import lru_cache
from chromadb import PersistentClient
from chromadb.config import Settings as ChromaSettings
from backend.config.settings import get_settings


@lru_cache(maxsize=1)
def get_chroma() -> PersistentClient: # type: ignore
    """Return a cached ChromaDB persistent client."""
    settings = get_settings()
    return PersistentClient(
        path=settings.chroma_persist_dir,
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def create_chroma_collection(collection_id: str, metadata: dict | None = None) -> None:
    """
    Create a ChromaDB collection keyed by the Supabase collection UUID.
    Called immediately after the Supabase row is inserted.
    """
    client = get_chroma()
    client.get_or_create_collection(
        name=collection_id,
        metadata=metadata or {},
    )


def delete_chroma_collection(collection_id: str) -> None:
    """
    Delete the ChromaDB collection. Safe to call even if it doesn't exist.
    Called immediately before or after the Supabase row is deleted.
    """
    client = get_chroma()
    try:
        client.delete_collection(name=collection_id)
    except Exception:
        pass


def get_chroma_collection(collection_id: str):
    """Return the ChromaDB collection object for querying / adding documents."""
    client = get_chroma()
    return client.get_collection(name=collection_id)