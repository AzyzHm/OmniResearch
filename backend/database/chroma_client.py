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


def add_item_chunks(
    collection_id: str,
    item_id: str,
    chunks: list[str],
    embeddings: list[list[float]],
    source_name: str,
) -> None:
    """
    Add one collection_items row's chunks to its parent Chroma collection.

    Each chunk is stored with both its raw text (documents) and its vector
    (embeddings), and tagged with item_id/chunk_index metadata so it can be
    filtered or deleted per-item later (toggle include/exclude, delete file).
    """
    collection = get_chroma_collection(collection_id)
    collection.add(
        ids=[f"{item_id}_{i}" for i in range(len(chunks))],
        documents=chunks,
        embeddings=embeddings,
        metadatas=[
            {
                "item_id": item_id,
                "collection_id": collection_id,
                "source_name": source_name,
                "chunk_index": i,
            }
            for i in range(len(chunks))
        ],
    )


def delete_item_chunks(collection_id: str, item_id: str) -> None:
    """Delete all chunks belonging to one item from its parent Chroma collection."""
    try:
        collection = get_chroma_collection(collection_id)
        collection.delete(where={"item_id": item_id})
    except Exception:
        pass