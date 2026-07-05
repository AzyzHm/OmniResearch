from typing import Optional

from backend.database.db import get_supabase


def record_llm_usage(
    user_id: Optional[str],
    provider: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
) -> None:
    """
    Log one LLM call for the usage-monitoring admin view. Best-effort: a
    failure here must never break the actual chat response, so any error
    is caught and printed rather than raised.
    """
    if not user_id:
        return
    try:
        db = get_supabase()
        db.table("llm_usage").insert({
            "user_id": user_id,
            "provider": provider,
            "model": model,
            "prompt_tokens": prompt_tokens or 0,
            "completion_tokens": completion_tokens or 0,
            "total_tokens": total_tokens or 0,
        }).execute()
    except Exception as exc:
        print(f"[USAGE] Failed to record LLM usage: {exc}")


def record_search_usage(
    user_id: Optional[str],
    engine: str,
    num_results: int,
    search_depth: Optional[str] = None,
) -> None:
    """
    Log one web-search call for the usage-monitoring admin view. Best-effort.

    credits: Tavily's "advanced" search_depth costs roughly double a normal
    call, so it's weighted as 2 credits here; everything else (Tavily
    basic/fast/ultra-fast, all Exa calls) is weighted as 1.
    """
    if not user_id:
        return
    credits = 2 if engine == "tavily" and search_depth == "advanced" else 1
    try:
        db = get_supabase()
        db.table("search_usage").insert({
            "user_id": user_id,
            "engine": engine,
            "num_results": num_results or 0,
            "search_depth": search_depth,
            "credits": credits,
        }).execute()
    except Exception as exc:
        print(f"[USAGE] Failed to record search usage: {exc}")