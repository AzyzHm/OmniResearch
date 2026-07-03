from backend.graph.state import RAGState
from backend.services.rag_retrieval import retrieve_pool

POOL_SIZE = 10
BATCH_SIZE = 5


def retrieve_node(state: RAGState) -> dict:
    attempts = state.get("retrieval_attempts", 0)
    print(f"[RAG] retrieve_node: attempt {attempts + 1}")

    if attempts == 0:
        pool = retrieve_pool(
            project_id=state["project_id"],
            query=state.get("refined_query") or state["query"],
            pool_size=POOL_SIZE,
        )
        print(f"[RAG] retrieve_node: pool size = {len(pool)}")
        return {
            "retrieved_pool": pool,
            "context_chunks": pool[:BATCH_SIZE],
            "retrieval_attempts": attempts + 1,
            "validation_passed": len(pool) == 0,
        }

    pool = state.get("retrieved_pool", [])
    next_batch = pool[BATCH_SIZE : BATCH_SIZE * 2]
    context_chunks = state.get("context_chunks", []) + next_batch
    print(f"[RAG] retrieve_node: added {len(next_batch)} more chunk(s), total {len(context_chunks)}")
    return {
        "context_chunks": context_chunks,
        "retrieval_attempts": attempts + 1,
    }