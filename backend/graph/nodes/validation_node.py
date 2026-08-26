import logging

from graph.state import RAGState
from services.rag_llm import validate_context

logger = logging.getLogger(__name__)


def validation_node(state: RAGState) -> dict:
    if state.get("validation_passed"):
        logger.info("validation_node: skipped (empty pool)")
        return {"validation_passed": True}

    passed, missing_query = validate_context(state["query"], state.get("context_chunks", []), user_id=state["user_id"])
    if passed:
        logger.info("validation_node: passed = True")
        return {"validation_passed": True, "missing_query": None}

    logger.info("validation_node: passed = False, missing = %r", missing_query)
    return {"validation_passed": False, "missing_query": missing_query}
