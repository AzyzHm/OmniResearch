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


def _own_note(note_id: str, user_id: str) -> dict:
    """Fetch a note and verify ownership through its project. Returns the note row."""
    db = get_supabase()
    result = (
        db.table("notes")
        .select("*, projects(user_id)")
        .eq("id", note_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found.")
    row: Any = result.data[0]
    project: Any = row.get("projects") or {}
    if project.get("user_id") != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found.")
    return row


def _existing_note_names(project_id: str, exclude_id: str | None = None) -> list[str]:
    """Names of the project's other notes, used to silently dedupe on create/rename."""
    db = get_supabase()
    query = db.table("notes").select("id, name").eq("project_id", project_id)
    if exclude_id is not None:
        query = query.neq("id", exclude_id)
    result = query.execute()
    return [row["name"] for row in result.data]  # type: ignore


def _own_message_in_project(message_id: str, project_id: str) -> dict:
    """
    Fetch a message and verify, through its chat, that it belongs to the given
    project — prevents saving a message from someone else's (or another
    project's) chat into this note. Returns the message row with chat_id.
    """
    db = get_supabase()
    result = (
        db.table("messages")
        .select("*, chats(project_id)")
        .eq("id", message_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found.")
    row: Any = result.data[0]
    chat: Any = row.get("chats") or {}
    if chat.get("project_id") != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found.")
    return row