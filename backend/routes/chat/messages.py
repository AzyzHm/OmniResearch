from fastapi import APIRouter, Depends

from backend.config.auth import get_current_user
from backend.config.settings import get_settings
from backend.database.db import get_supabase
from backend.models.chat import MessageOut
from backend.routes.chat._shared import _own_chat

router = APIRouter()


@router.get("/chats/{chat_id}/messages", response_model=list[MessageOut])
async def get_messages(
    chat_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Return the most recent ui_history_limit messages for a chat, oldest first."""
    _own_chat(chat_id, current_user["sub"])
    db = get_supabase()
    settings = get_settings()

    result = (
        db.table("messages")
        .select("id, chat_id, role, content, created_at")
        .eq("chat_id", chat_id)
        .order("created_at", desc=True)
        .limit(settings.ui_history_limit)
        .execute()
    )
    return list(reversed(result.data))