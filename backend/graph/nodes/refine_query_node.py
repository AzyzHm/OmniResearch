import logging

from graph.state import RAGState
from services.rag_llm import refine_query

logger = logging.getLogger(__name__)


def refine_query_node(state: RAGState) -> dict:
    refined = refine_query(state.get("history", []), state["query"], user_id=state["user_id"])
    logger.info("refine_query_node: refined = %r", refined)
    return {"refined_query": refined}