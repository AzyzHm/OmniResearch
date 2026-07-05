from backend.graph.state import RAGState
from backend.services.rag_llm import refine_query


def refine_query_node(state: RAGState) -> dict:
    refined = refine_query(state.get("history", []), state["query"], user_id=state["user_id"])
    print(f"[RAG] refine_query_node: refined = {refined!r}")
    return {"refined_query": refined}