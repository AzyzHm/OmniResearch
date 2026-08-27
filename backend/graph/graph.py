from langgraph.graph import END, StateGraph

from backend.graph.nodes.generate_node import generate_node
from backend.graph.nodes.refine_query_node import refine_query_node
from backend.graph.nodes.rerank_node import rerank_node
from backend.graph.nodes.retrieve_node import retrieve_node
from backend.graph.nodes.router_node import router_node
from backend.graph.nodes.validation_node import validation_node
from backend.graph.state import RAGState

MAX_RETRIEVAL_ATTEMPTS = 3


def _after_router(state: RAGState) -> str:
    return "refine_query" if state.get("needs_retrieval") else "generate"


def _after_validation(state: RAGState) -> str:
    if state.get("validation_passed"):
        return "generate"
    if state.get("retrieval_attempts", 0) >= MAX_RETRIEVAL_ATTEMPTS:
        return "generate"
    return "retrieve"


def build_rag_graph():
    graph = StateGraph(RAGState)

    graph.add_node("router", router_node)
    graph.add_node("refine_query", refine_query_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("rerank", rerank_node)
    graph.add_node("validate", validation_node)
    graph.add_node("generate", generate_node)

    graph.set_entry_point("router")

    graph.add_conditional_edges(
        "router",
        _after_router,
        {"refine_query": "refine_query", "generate": "generate"},
    )
    graph.add_edge("refine_query", "retrieve")
    graph.add_edge("retrieve", "rerank")
    graph.add_edge("rerank", "validate")
    graph.add_conditional_edges(
        "validate",
        _after_validation,
        {"generate": "generate", "retrieve": "retrieve"},
    )
    graph.add_edge("generate", END)

    return graph.compile()


_compiled_graph = None


def get_rag_graph():
    """Compile once, reuse across requests."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_rag_graph()
    return _compiled_graph