from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from backend.config.auth import require_admin
from backend.database.db import get_supabase
from backend.models import MessageResponse, TokenLimitUpdate

router = APIRouter()


@router.put(
    "/users/{user_id}/token-limit",
    response_model=MessageResponse,
    summary="Change a user's daily LLM token quota (regular users only)",
)
async def change_token_limit(
    user_id: str,
    body: TokenLimitUpdate,
    _: dict = Depends(require_admin),
):
    db = get_supabase()

    result: Any = db.table("users").select("id, username, role").eq("id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    target = result.data[0]
    if target["role"] != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Daily token limits only apply to regular user accounts.",
        )

    db.table("users").update({"daily_token_limit": body.daily_token_limit}).eq("id", user_id).execute()
    return MessageResponse(
        message=f"Daily token limit for '{target['username']}' updated to {body.daily_token_limit:,}."
    )