from typing import Any

from fastapi import HTTPException, status

from backend.database.db import get_supabase


def _verify_project_owner(project_id: str, user_id: str) -> None:
    """Raise 404 if the project doesn't belong to the user."""
    db = get_supabase()
    result = (
        db.table("projects")
        .select("id")
        .eq("id", project_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")


def _own_chat(chat_id: str, user_id: str) -> dict:
    """
    Fetch a chat and verify through its project that it belongs to the user.
    Returns the chat row.
    """
    db = get_supabase()
    result = (
        db.table("chats")
        .select("*, projects(user_id)")
        .eq("id", chat_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found.")
    row: Any = result.data[0]
    project: Any = row.get("projects") or {}
    if project.get("user_id") != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found.")
    return row