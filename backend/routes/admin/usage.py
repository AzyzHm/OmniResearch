from typing import Any, cast

from fastapi import APIRouter, Depends

from backend.config.auth import require_admin
from backend.database.db import get_supabase

router = APIRouter()


@router.get(
    "/usage/llm",
    summary="Aggregate per-user LLM token usage (Gemini + Mistral)",
)
async def get_llm_usage(_: dict = Depends(require_admin)):
    db = get_supabase()

    users_result = db.table("users").select("id, username").execute()
    username_by_id = {u["id"]: u["username"] for u in cast(list[Any], users_result.data)}

    usage_result = (
        db.table("llm_usage")
        .select("user_id, provider, prompt_tokens, completion_tokens, total_tokens")
        .order("created_at", desc=True)
        .limit(10000)
        .execute()
    )

    per_user: dict[str, dict[str, Any]] = {}
    for row in cast(list[dict[str, Any]], usage_result.data):
        uid = row["user_id"]
        bucket = per_user.setdefault(uid, {
            "user_id": uid,
            "username": username_by_id.get(uid, "Unknown"),
            "gemini_calls": 0, "gemini_tokens": 0,
            "mistral_calls": 0, "mistral_tokens": 0,
            "total_calls": 0, "total_tokens": 0,
        })
        provider = row["provider"]
        tokens = row.get("total_tokens", 0) or 0
        bucket[f"{provider}_calls"] += 1
        bucket[f"{provider}_tokens"] += tokens
        bucket["total_calls"] += 1
        bucket["total_tokens"] += tokens

    rows = sorted(per_user.values(), key=lambda r: r["total_tokens"], reverse=True)
    return {"users": rows}


@router.get(
    "/usage/search",
    summary="Aggregate per-user search engine usage (Tavily + Exa)",
)
async def get_search_usage(_: dict = Depends(require_admin)):
    db = get_supabase()

    users_result = db.table("users").select("id, username").execute()
    username_by_id = {u["id"]: u["username"] for u in cast(list[Any], users_result.data)}

    usage_result = (
        db.table("search_usage")
        .select("user_id, engine, num_results, credits")
        .order("created_at", desc=True)
        .limit(10000)
        .execute()
    )

    per_user: dict[str, dict[str, Any]] = {}
    for row in cast(list[dict[str, Any]], usage_result.data):
        uid = row["user_id"]
        bucket = per_user.setdefault(uid, {
            "user_id": uid,
            "username": username_by_id.get(uid, "Unknown"),
            "tavily_calls": 0, "tavily_credits": 0,
            "exa_calls": 0, "exa_credits": 0,
            "total_calls": 0, "total_credits": 0,
        })
        engine = row["engine"]
        credits = row.get("credits", 1) or 1
        bucket[f"{engine}_calls"] += 1
        bucket[f"{engine}_credits"] += credits
        bucket["total_calls"] += 1
        bucket["total_credits"] += credits

    rows = sorted(per_user.values(), key=lambda r: r["total_credits"], reverse=True)
    return {"users": rows}