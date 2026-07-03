from backend.graph.state import RAGState
from backend.services.rag_llm import generate_answer


def generate_node(state: RAGState) -> dict:
    print(f"[RAG] generate_node: context_chunks = {len(state.get('context_chunks', []))}")
    answer = generate_answer(
        history=state.get("history", []),
        query=state["query"],
        context_chunks=state.get("context_chunks", []),
    )
    print("[RAG] generate_node: done")
    return {"answer": answer}