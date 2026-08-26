import logging

from graph.state import RAGState
from services.rag_llm import decide_retrieval

logger = logging.getLogger(__name__)


def router_node(state: RAGState) -> dict:
    needs_retrieval = decide_retrieval(state.get("history", []), state["query"], user_id=state["user_id"])
    logger.info("router_node: needs_retrieval = %s", needs_retrieval)
    return {"needs_retrieval": needs_retrieval}
