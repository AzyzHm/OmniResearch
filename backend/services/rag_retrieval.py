from typing import Any, cast

from backend.database.chroma_client import get_chroma_collection
from backend.database.db import get_supabase
from backend.services.embeddings import embed_texts


def get_active_items_by_collection(project_id: str) -> dict[str, list[str]]:
    """Return {collection_id: [item_id, ...]} for every ready + active item in a project."""
    db = get_supabase()

    collections_result = (
        db.table("collections").select("id").eq("project_id", project_id).execute()
    )
    collection_rows = cast(list[dict[str, Any]], collections_result.data)
    collection_ids = [row["id"] for row in collection_rows]
    if not collection_ids:
        return {}

    items_result = (
        db.table("collection_items")
        .select("id, collection_id")
        .in_("collection_id", collection_ids)
        .eq("is_active", True)
        .eq("status", "ready")
        .execute()
    )
    item_rows = cast(list[dict[str, Any]], items_result.data)

    by_collection: dict[str, list[str]] = {}
    for row in item_rows:
        by_collection.setdefault(row["collection_id"], []).append(row["id"])
    return by_collection


def retrieve_pool(project_id: str, query: str, pool_size: int = 10) -> list[dict[str, Any]]:
    """
    Embed the query once, search every collection that has active items, and
    return up to pool_size chunks globally sorted by similarity (lowest
    distance first). Callers slice this list into batches (e.g. [0:5], then
    [5:10]) without needing to re-embed or re-query.
    """
    active_by_collection = get_active_items_by_collection(project_id)
    if not active_by_collection:
        return []

    query_vector = embed_texts([query])[0]

    pooled: list[dict[str, Any]] = []

    for collection_id, item_ids in active_by_collection.items():
        try:
            chroma_collection = get_chroma_collection(collection_id)
        except Exception:
            continue

        result = chroma_collection.query(
            query_embeddings=[query_vector],
            n_results=pool_size,
            where={"item_id": {"$in": item_ids}},
        )

        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]

        for doc, meta, dist in zip(documents, metadatas, distances):
            meta = meta or {}
            pooled.append({
                "content": doc,
                "source_name": meta.get("source_name", "unknown source"),
                "collection_id": collection_id,
                "item_id": meta.get("item_id"),
                "distance": dist,
            })

    pooled.sort(key=lambda c: c["distance"])
    return pooled[:pool_size]