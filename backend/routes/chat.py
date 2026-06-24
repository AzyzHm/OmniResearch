"""
routes/chats.py – Chat CRUD and Gemini test message endpoint.

Structure
─────────
GET    /projects/{project_id}/chats          → list chats in a project
POST   /projects/{project_id}/chats          → create chat
PUT    /chats/{chat_id}                      → rename chat
DELETE /chats/{chat_id}                      → delete chat
POST   /chats/{chat_id}/message              → send message → Gemini → response
"""
from typing import Any

from backend.config.models import get_gemini_response
from fastapi import APIRouter, Depends, HTTPException, status

from backend.config.auth import get_current_user
from backend.database.db import get_supabase
from backend.models.chat import (
    ChatCreate,
    ChatMessageRequest,
    ChatMessageResponse,
    ChatOut,
    ChatUpdate,
)

router = APIRouter(tags=["Chats"])


# ── Helpers ───────────────────────────────────────────────────────────────────

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
    # Join via projects table
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


# ── List ──────────────────────────────────────────────────────────────────────

@router.get("/projects/{project_id}/chats", response_model=list[ChatOut])
async def list_chats(
    project_id: str,
    current_user: dict = Depends(get_current_user),
):
    _verify_project_owner(project_id, current_user["sub"])
    db = get_supabase()
    result = (
        db.table("chats")
        .select("id, project_id, name, created_at")
        .eq("project_id", project_id)
        .order("created_at", desc=False)
        .execute()
    )
    return result.data


# ── Create ────────────────────────────────────────────────────────────────────

@router.post(
    "/projects/{project_id}/chats",
    response_model=ChatOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_chat(
    project_id: str,
    body: ChatCreate,
    current_user: dict = Depends(get_current_user),
):
    _verify_project_owner(project_id, current_user["sub"])
    db = get_supabase()
    result = db.table("chats").insert(
        {"project_id": project_id, "name": body.name}
    ).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create chat.")
    row: Any = result.data[0]
    return row


# ── Rename ────────────────────────────────────────────────────────────────────

@router.put("/chats/{chat_id}", response_model=ChatOut)
async def rename_chat(
    chat_id: str,
    body: ChatUpdate,
    current_user: dict = Depends(get_current_user),
):
    _own_chat(chat_id, current_user["sub"])
    db = get_supabase()
    result = (
        db.table("chats")
        .update({"name": body.name})
        .eq("id", chat_id)
        .execute()
    )
    row: Any = result.data[0]
    return row


# ── Delete ────────────────────────────────────────────────────────────────────

@router.delete("/chats/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    chat_id: str,
    current_user: dict = Depends(get_current_user),
):
    _own_chat(chat_id, current_user["sub"])
    db = get_supabase()
    db.table("chats").delete().eq("id", chat_id).execute()


# ── Send message → Gemini ─────────────────────────────────────────────────────

@router.post("/chats/{chat_id}/message", response_model=ChatMessageResponse)
async def send_message(
    chat_id: str,
    body: ChatMessageRequest,
    current_user: dict = Depends(get_current_user),
):
    _own_chat(chat_id, current_user["sub"])

    history = [{"role": e.role, "content": e.content} for e in body.history]

    try:
        reply = get_gemini_response(body.message, history)
        return ChatMessageResponse(response=reply)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini error: {exc}",
        )