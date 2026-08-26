from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, status

from config.auth import get_current_user
from database.db import get_supabase
from models.note import NoteItemCreate, NoteItemOut
from routes.notes._shared import _own_message_in_project, _own_note

router = APIRouter()


def _flatten_item(row: dict) -> dict:
    """note_items row (with embedded `messages`) -> flat NoteItemOut shape."""
    message: Any = row.get("messages") or {}
    return {
        "id": row["id"],
        "note_id": row["note_id"],
        "message_id": row["message_id"],
        "chat_id": message.get("chat_id"),
        "role": message.get("role"),
        "content": message.get("content"),
        "sources": message.get("sources"),
        "created_at": row["created_at"],
    }


@router.get("/notes/{note_id}/items", response_model=list[NoteItemOut])
async def list_note_items(
    note_id: str,
    current_user: dict = Depends(get_current_user),
):
    _own_note(note_id, current_user["sub"])
    db = get_supabase()
    result = (
        db.table("note_items")
        .select("id, note_id, message_id, created_at, messages(chat_id, role, content, sources)")
        .eq("note_id", note_id)
        .order("created_at", desc=False)
        .execute()
    )
    return [_flatten_item(row) for row in cast(list[dict[str, Any]], result.data)]


@router.post(
    "/notes/{note_id}/items",
    response_model=NoteItemOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_note_item(
    note_id: str,
    body: NoteItemCreate,
    current_user: dict = Depends(get_current_user),
):
    """Save a chat message (with its sources) into a note."""
    note = _own_note(note_id, current_user["sub"])
    message = _own_message_in_project(body.message_id, note["project_id"])
    db = get_supabase()

    existing = db.table("note_items").select("id").eq("note_id", note_id).eq("message_id", body.message_id).execute()
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This message is already saved to this note.",
        )

    result = db.table("note_items").insert({"note_id": note_id, "message_id": body.message_id}).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to save message to note.")

    row: Any = result.data[0]
    return {
        "id": row["id"],
        "note_id": row["note_id"],
        "message_id": row["message_id"],
        "chat_id": message.get("chat_id"),
        "role": message.get("role"),
        "content": message.get("content"),
        "sources": message.get("sources"),
        "created_at": row["created_at"],
    }


@router.delete(
    "/notes/{note_id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_note_item(
    note_id: str,
    item_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Unsave a message from a note, without deleting the note itself."""
    _own_note(note_id, current_user["sub"])
    db = get_supabase()
    db.table("note_items").delete().eq("id", item_id).eq("note_id", note_id).execute()
