from backend.config.settings import get_settings
from backend.graph.state import RAGState
from backend.services.reranker import rerank


def _chunk_key(chunk: dict) -> tuple:
    return (chunk.get("collection_id"), chunk.get("item_id"), chunk["content"])


def rerank_node(state: RAGState) -> dict:
    """
    Re-scores this round's retrieval pool against the query that produced it
    (the missing-info query on a retry, or the refined query on the first
    pass) using the BAAI/bge-reranker-base cross-encoder, keeps the top
    rerank_top_k, and merges them into whatever context was already accepted
    from earlier rounds — de-duplicating so the same chunk never counts
    twice toward the context sent to generation.
    """
    settings = get_settings()
    pool = state.get("retrieved_pool", [])
    existing = state.get("context_chunks", [])

    if not pool:
        print("[RAG] rerank_node: empty pool, nothing to rerank")
        return {"context_chunks": existing}

    query = state.get("missing_query") or state.get("refined_query") or state["query"]
    is_retry = bool(state.get("missing_query"))
    print(f"[RAG] rerank_node: reranking {len(pool)} candidate(s) for the "
          f"{'follow-up' if is_retry else 'initial'} query")

    top_chunks = rerank(query, pool, top_k=settings.rerank_top_k)

    seen = {_chunk_key(c) for c in existing}
    merged = list(existing)
    added = 0
    for chunk in top_chunks:
        key = _chunk_key(chunk)
        if key not in seen:
            merged.append(chunk)
            seen.add(key)
            added += 1

    print(f"[RAG] rerank_node: kept {added} new chunk(s) (of {len(top_chunks)} reranked), "
          f"total context now {len(merged)}")
    return {"context_chunks": merged}