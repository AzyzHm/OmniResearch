import re

from backend.graph.state import RAGState
from backend.services.rag_llm import generate_answer

NO_SOURCES_MESSAGE = (
    "There are no active sources to search in this project. Add a document, "
    "text file, or URL to a collection (and make sure at least one is toggled "
    "on), then ask again."
)

_CITATION_RE = re.compile(r"\[(\d+)\]")


def _extract_cited_sources(answer: str, context_chunks: list[dict]) -> list[dict]:
    """
    Finds every [n] marker the model actually used in its answer and maps it
    back to the numbered context block it refers to (context_chunks is
    1-indexed in the prompt, matching _format_context in rag_llm.py).
    Ignores out-of-range numbers rather than raising, since an LLM
    occasionally hallucinates a citation number that doesn't exist.
    """
    cited_indices: list[int] = []
    seen = set()
    for match in _CITATION_RE.finditer(answer):
        n = int(match.group(1))
        if n not in seen and 1 <= n <= len(context_chunks):
            seen.add(n)
            cited_indices.append(n)

    sources = []
    for n in cited_indices:
        chunk = context_chunks[n - 1]
        sources.append({
            "index": n,
            "source_name": chunk.get("source_name", "unknown source"),
            "collection_id": chunk.get("collection_id"),
            "item_id": chunk.get("item_id"),
        })
    return sources


def generate_node(state: RAGState) -> dict:
    if state.get("needs_retrieval") and not state.get("context_chunks"):
        print("[RAG] generate_node: retrieval requested but no sources available — skipping LLM call")
        return {"answer": NO_SOURCES_MESSAGE, "sources": []}

    context_chunks = state.get("context_chunks", [])
    print(f"[RAG] generate_node: context_chunks = {len(context_chunks)}")
    answer = generate_answer(
        history=state.get("history", []),
        query=state["query"],
        context_chunks=context_chunks,
        user_id=state["user_id"],
    )
    sources = _extract_cited_sources(answer, context_chunks)
    print(f"[RAG] generate_node: done, {len(sources)} source(s) cited")
    return {"answer": answer, "sources": sources}