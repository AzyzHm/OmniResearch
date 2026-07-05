from backend.graph.state import RAGState
from backend.services.rag_llm import decide_retrieval


def router_node(state: RAGState) -> dict:
    needs_retrieval = decide_retrieval(state.get("history", []), state["query"], user_id=state["user_id"])
    print(f"[RAG] router_node: needs_retrieval = {needs_retrieval}")
    return {"needs_retrieval": needs_retrieval}