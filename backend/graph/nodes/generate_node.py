from backend.graph.state import RAGState
from backend.services.rag_llm import generate_answer

NO_SOURCES_MESSAGE = (
    "There are no active sources to search in this project. Add a document, "
    "text file, or URL to a collection (and make sure at least one is toggled "
    "on), then ask again."
)


def generate_node(state: RAGState) -> dict:
    if state.get("needs_retrieval") and not state.get("context_chunks"):
        print("[RAG] generate_node: retrieval requested but no sources available — skipping LLM call")
        return {"answer": NO_SOURCES_MESSAGE}

    print(f"[RAG] generate_node: context_chunks = {len(state.get('context_chunks', []))}")
    answer = generate_answer(
        history=state.get("history", []),
        query=state["query"],
        context_chunks=state.get("context_chunks", []),
        user_id=state["user_id"],
    )
    print("[RAG] generate_node: done")
    return {"answer": answer}