from backend.graph.state import RAGState
from backend.services.rag_llm import validate_context


def validation_node(state: RAGState) -> dict:
    if state.get("validation_passed"):
        print("[RAG] validation_node: skipped (empty pool)")
        return {"validation_passed": True}
    passed = validate_context(state["query"], state.get("context_chunks", []), user_id=state["user_id"])
    print(f"[RAG] validation_node: passed = {passed}")
    return {"validation_passed": passed}