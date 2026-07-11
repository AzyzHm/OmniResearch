from typing import Any, Literal, cast

from backend.database.chroma_client import get_chroma_collection
from backend.database.db import get_supabase
from backend.services.bm25 import bm25_sparse_vector, sparse_dot, sparse_vector_from_metadata
from backend.services.embeddings import embed_texts

RetrievalMode = Literal["semantic", "keyword", "hybrid"]
RRF_K = 60


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


def _fetch_all_active_chunks(project_id: str) -> list[dict[str, Any]]:
    """
    Fetch every chunk (document + metadata) for every active/ready item in a
    project, across all its collections — a plain Chroma `get()`, not a
    vector search. Used by keyword/hybrid retrieval, which need to score
    every candidate chunk in Python rather than use Chroma's dense ANN index
    (Chroma's own hybrid ranking API is Chroma-Cloud-only — see
    backend/services/bm25.py for why this is done manually here).
    """
    active_by_collection = get_active_items_by_collection(project_id)
    if not active_by_collection:
        return []

    chunks: list[dict[str, Any]] = []
    for collection_id, item_ids in active_by_collection.items():
        try:
            chroma_collection = get_chroma_collection(collection_id)
        except Exception:
            continue

        result = chroma_collection.get(
            where={"item_id": {"$in": item_ids}},
            include=["documents", "metadatas"],
        )
        documents = result.get("documents") or []
        metadatas = result.get("metadatas") or []

        for doc, meta in zip(documents, metadatas):
            meta = meta or {}
            bm25_indices, bm25_values = sparse_vector_from_metadata(meta)
            chunks.append({
                "content": doc,
                "source_name": meta.get("source_name", "unknown source"),
                "collection_id": collection_id,
                "item_id": meta.get("item_id"),
                "_bm25_indices": bm25_indices,
                "_bm25_values": bm25_values,
            })
    return chunks


def _retrieve_pool_semantic(project_id: str, query: str, pool_size: int) -> list[dict[str, Any]]:
    """Dense vector nearest-neighbor retrieval — the original default strategy."""
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
                "distance": dist,  # lower = more relevant
            })

    pooled.sort(key=lambda c: c["distance"])
    return pooled[:pool_size]


def _retrieve_pool_keyword(project_id: str, query: str, pool_size: int) -> list[dict[str, Any]]:
    """
    BM25 keyword retrieval. Scores every active chunk in the project against
    the query's BM25 sparse vector via a manual sparse dot product, and keeps
    only chunks that actually share at least one term with the query.
    """
    chunks = _fetch_all_active_chunks(project_id)
    if not chunks:
        return []

    query_sv = bm25_sparse_vector(query)
    q_indices, q_values = list(query_sv.indices), list(query_sv.values)

    scored: list[dict[str, Any]] = []
    for chunk in chunks:
        score = sparse_dot(q_indices, q_values, chunk["_bm25_indices"], chunk["_bm25_values"])
        if score <= 0:
            continue
        scored.append({
            "content": chunk["content"],
            "source_name": chunk["source_name"],
            "collection_id": chunk["collection_id"],
            "item_id": chunk["item_id"],
            "distance": -score,
        })

    scored.sort(key=lambda c: c["distance"])
    return scored[:pool_size]


def _retrieve_pool_hybrid(project_id: str, query: str, pool_size: int) -> list[dict[str, Any]]:
    """
    Combine semantic and keyword rankings via Reciprocal Rank Fusion (RRF) —
    the same fusion strategy Chroma's own Rrf() helper uses on Chroma Cloud,
    computed manually here since that helper isn't available for a local,
    self-hosted Chroma instance. Each ranking contributes 1/(RRF_K + rank)
    per chunk; chunks found by both rankings naturally score higher.
    """
    semantic_pool = _retrieve_pool_semantic(project_id, query, pool_size * 2)
    keyword_pool = _retrieve_pool_keyword(project_id, query, pool_size * 2)

    def _key(chunk: dict[str, Any]) -> tuple:
        return (chunk["collection_id"], chunk["item_id"], chunk["content"])

    rrf_scores: dict[tuple, float] = {}
    chunk_by_key: dict[tuple, dict[str, Any]] = {}

    for rank, chunk in enumerate(semantic_pool):
        key = _key(chunk)
        rrf_scores[key] = rrf_scores.get(key, 0.0) + 1.0 / (RRF_K + rank + 1)
        chunk_by_key[key] = chunk

    for rank, chunk in enumerate(keyword_pool):
        key = _key(chunk)
        rrf_scores[key] = rrf_scores.get(key, 0.0) + 1.0 / (RRF_K + rank + 1)
        chunk_by_key.setdefault(key, chunk)

    fused: list[dict[str, Any]] = []
    for key, score in rrf_scores.items():
        chunk = dict(chunk_by_key[key])
        chunk["distance"] = -score 
        fused.append(chunk)

    fused.sort(key=lambda c: c["distance"])
    return fused[:pool_size]


def retrieve_pool(
    project_id: str,
    query: str,
    pool_size: int = 10,
    mode: RetrievalMode = "semantic",
) -> list[dict[str, Any]]:
    """
    Score/embed the query once and return up to pool_size chunks, globally
    ranked across every active source in the project. `mode` selects the
    ranking strategy:
      - "semantic": dense vector similarity (the original default).
      - "keyword":  BM25 lexical scoring.
      - "hybrid":   Reciprocal Rank Fusion of both.
    Callers slice this list into batches (e.g. [0:5], then [5:10]) without
    needing to re-embed/re-score.
    """
    if mode == "keyword":
        return _retrieve_pool_keyword(project_id, query, pool_size)
    if mode == "hybrid":
        return _retrieve_pool_hybrid(project_id, query, pool_size)
    return _retrieve_pool_semantic(project_id, query, pool_size)