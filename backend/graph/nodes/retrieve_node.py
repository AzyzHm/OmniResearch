from typing import cast

from backend.config.settings import get_settings
from backend.graph.state import RAGState
from backend.services.rag_retrieval import RetrievalMode, retrieve_pool


def retrieve_node(state: RAGState) -> dict:
    """
    Fetches a wide candidate pool (default 50 chunks) for the current
    round's query — the initial refined query on the first pass, or the
    validator's "what's missing" follow-up query on a retry — and hands it
    to rerank_node to pick the best few. Unlike the old batch-slicing
    design, every attempt does a fresh retrieval against its own query
    rather than pulling more chunks from a single cached pool, since a
    follow-up query is deliberately different from the original one.
    """
    settings = get_settings()
    attempts = state.get("retrieval_attempts", 0)
    mode = state.get("retrieval_mode", "semantic")
    existing_context = state.get("context_chunks", [])


    query = state.get("missing_query") or state.get("refined_query") or state["query"]
    print(f"[RAG] retrieve_node: attempt {attempts + 1}, mode = {mode}, query = {query!r}")

    pool = retrieve_pool(
        project_id=state["project_id"],
        query=query,
        pool_size=settings.retrieval_pool_size,
        mode=cast(RetrievalMode, mode),
    )
    print(f"[RAG] retrieve_node: pool size = {len(pool)}")

    return {
        "retrieved_pool": pool,
        "retrieval_attempts": attempts + 1,
        "validation_passed": len(pool) == 0 and not existing_context,
    }