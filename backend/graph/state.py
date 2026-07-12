from typing import Any, TypedDict


class _RAGStateRequired(TypedDict):
    project_id: str
    chat_id: str
    user_id: str             
    query: str
    history: list[dict[str, Any]]
    retrieval_mode: str


class RAGState(_RAGStateRequired, total=False):
    refined_query: str
    missing_query: str

    needs_retrieval: bool

    retrieved_pool: list[dict[str, Any]]
    context_chunks: list[dict[str, Any]]
    retrieval_attempts: int
    validation_passed: bool

    answer: str