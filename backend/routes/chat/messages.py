from fastapi import APIRouter, Depends

from config.auth import get_current_user
from config.settings import get_settings
from database.db import get_supabase
from models.chat import MessageOut
from routes.chat._shared import _own_chat

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
        .select("id, chat_id, role, content, created_at, sources")
        .eq("chat_id", chat_id)
        .order("created_at", desc=True)
        .limit(settings.ui_history_limit)
        .execute()
    )
    return list(reversed(result.data))