import logging

from config.settings import get_settings
from graph.state import RAGState
from services.reranker import rerank

logger = logging.getLogger(__name__)


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
        logger.info("rerank_node: empty pool, nothing to rerank")
        return {"context_chunks": existing}

    query = state.get("missing_query") or state.get("refined_query") or state["query"]
    is_retry = bool(state.get("missing_query"))
    logger.info(
        "rerank_node: reranking %d candidate(s) for the %s query",
        len(pool),
        "follow-up" if is_retry else "initial",
    )

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

    logger.info(
        "rerank_node: kept %d new chunk(s) (of %d reranked), total context now %d",
        added,
        len(top_chunks),
        len(merged),
    )
    return {"context_chunks": merged}
