from datetime import datetime, timedelta, timezone
from typing import Any, Optional, cast

from database.db import get_supabase

DEFAULT_DAILY_TOKEN_LIMIT = 80_000


def _start_of_today_utc() -> datetime:
    return datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)


def _start_of_tomorrow_utc() -> datetime:
    return _start_of_today_utc() + timedelta(days=1)


class DailyQuotaExceeded(Exception):
    """Raised when a user has used up their daily token quota. The message
    is user-facing and states exactly when the quota resets."""

    def __init__(self, used: int, limit: int, reset_at: datetime):
        self.used = used
        self.limit = limit
        self.reset_at = reset_at

        remaining = reset_at - datetime.now(timezone.utc)
        total_minutes = max(int(remaining.total_seconds() // 60), 0)
        hours, minutes = divmod(total_minutes, 60)
        self.user_message = (
            f"You've used all {limit:,} of your daily tokens ({used:,} used today). "
            f"Your quota resets at {reset_at.strftime('%Y-%m-%d %H:%M')} UTC "
            f"(in {hours}h {minutes}m)."
        )
        super().__init__(self.user_message)


def get_daily_token_limit(user_id: str) -> int:
    """Read a user's configured daily token limit (admin-editable), falling
    back to the default if the user row or column value is missing."""
    db = get_supabase()
    result = db.table("users").select("daily_token_limit").eq("id", user_id).execute()
    rows = cast(list[dict[str, Any]], result.data)
    if not rows:
        return DEFAULT_DAILY_TOKEN_LIMIT
    return rows[0].get("daily_token_limit") or DEFAULT_DAILY_TOKEN_LIMIT


def get_tokens_used_today(user_id: str) -> int:
    """Sum total_tokens from llm_usage for this user since UTC midnight."""
    db = get_supabase()
    start = _start_of_today_utc().isoformat()
    result = (
        db.table("llm_usage")
        .select("total_tokens")
        .eq("user_id", user_id)
        .gte("created_at", start)
        .execute()
    )
    rows = cast(list[dict[str, Any]], result.data) or []
    return sum((row.get("total_tokens") or 0) for row in rows)


def enforce_daily_quota(user_id: Optional[str], role: Optional[str] = None) -> None:
    """
    Raise DailyQuotaExceeded if this user has hit their daily token limit.

    Admins and superadmins are exempt — the admin panel already refuses to
    let anyone set a token limit for non-"user" roles, which only makes
    sense if quotas are meant to not apply to them in the first place.

    Call this BEFORE persisting the user's message or invoking the RAG graph,
    so an exhausted user is blocked immediately — no message is saved, no
    LLM call is attempted, and no tokens are spent on router/refine/validate
    calls before the block kicks in.
    """
    if not user_id or role in ("admin", "superadmin"):
        return
    limit = get_daily_token_limit(user_id)
    used = get_tokens_used_today(user_id)
    if used >= limit:
        raise DailyQuotaExceeded(used=used, limit=limit, reset_at=_start_of_tomorrow_utc())