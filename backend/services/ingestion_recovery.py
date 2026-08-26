import logging

from database.db import get_supabase

logger = logging.getLogger(__name__)

STUCK_PROCESSING_MESSAGE = "Interrupted by a server restart before ingestion finished. Please re-add this item."


def recover_stuck_processing_items() -> int:
    """
    Runs once at backend startup (see main.py's lifespan).

    File/URL/search-result ingestion runs as a FastAPI BackgroundTasks
    job: an in-process asyncio task with no persistence. If the server
    restarts (deploy, crash) while an item is mid-pipeline, that task is
    simply gone — the item is left stuck at status="processing" forever,
    with nothing to notice or recover it.

    Since this only runs at process startup, nothing can legitimately
    still be mid-flight yet: any item already "processing" at this point
    was orphaned by whatever caused the previous process to stop. Mark
    each one as an error so it's visible and the user can re-add it,
    rather than silently stuck.

    Returns the number of items recovered (0 in the common case, and also
    if the sweep itself fails — a DB hiccup at boot must not prevent the
    app from starting, so any error here is logged rather than raised).
    """
    db = get_supabase()
    try:
        result = (
            db.table("collection_items")
            .update(
                {
                    "status": "error",
                    "error_message": STUCK_PROCESSING_MESSAGE,
                }
            )
            .eq("status", "processing")
            .execute()
        )
    except Exception as exc:
        logger.error("Failed to sweep stuck 'processing' collection items: %s", exc)
        return 0

    recovered = len(result.data or []) if result is not None else 0
    if recovered:
        logger.warning(
            "Recovered %d collection item(s) stuck in 'processing' from a previous run.",
            recovered,
        )
    return recovered
