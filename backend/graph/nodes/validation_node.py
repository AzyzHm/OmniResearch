from backend.graph.state import RAGState
from backend.services.rag_llm import validate_context


def validation_node(state: RAGState) -> dict:
    if state.get("validation_passed"):
        print("[RAG] validation_node: skipped (empty pool)")
        return {"validation_passed": True}

    passed, missing_query = validate_context(
        state["query"], state.get("context_chunks", []), user_id=state["user_id"]
    )
    if passed:
        print("[RAG] validation_node: passed = True")
        return {"validation_passed": True, "missing_query": None}

    print(f"[RAG] validation_node: passed = False, missing = {missing_query!r}")
    return {"validation_passed": False, "missing_query": missing_query}