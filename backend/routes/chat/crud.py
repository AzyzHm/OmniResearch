from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from backend.config.auth import get_current_user
from backend.database.db import get_supabase
from backend.models.chat import ChatCreate, ChatOut, ChatUpdate
from backend.routes.chat._shared import _own_chat, _verify_project_owner

router = APIRouter()


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


@router.delete("/chats/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    chat_id: str,
    current_user: dict = Depends(get_current_user),
):
    _own_chat(chat_id, current_user["sub"])
    db = get_supabase()
    db.table("chats").delete().eq("id", chat_id).execute()