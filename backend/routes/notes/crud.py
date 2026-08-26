from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from config.auth import get_current_user
from database.db import get_supabase
from models.note import NoteCreate, NoteOut, NoteUpdate
from routes.notes._shared import _existing_note_names, _own_note, _verify_project_owner
from utils.naming import next_unique_name

router = APIRouter()


@router.get("/projects/{project_id}/notes", response_model=list[NoteOut])
async def list_notes(
    project_id: str,
    current_user: dict = Depends(get_current_user),
):
    _verify_project_owner(project_id, current_user["sub"])
    db = get_supabase()
    result = (
        db.table("notes")
        .select("id, project_id, name, created_at")
        .eq("project_id", project_id)
        .order("created_at", desc=False)
        .execute()
    )
    return result.data


@router.post(
    "/projects/{project_id}/notes",
    response_model=NoteOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_note(
    project_id: str,
    body: NoteCreate,
    current_user: dict = Depends(get_current_user),
):
    _verify_project_owner(project_id, current_user["sub"])
    db = get_supabase()

    existing_names = _existing_note_names(project_id)
    unique_name = next_unique_name(body.name, existing_names)

    result = db.table("notes").insert({"project_id": project_id, "name": unique_name}).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create note.")

    row: Any = result.data[0]
    return row


@router.put("/notes/{note_id}", response_model=NoteOut)
async def rename_note(
    note_id: str,
    body: NoteUpdate,
    current_user: dict = Depends(get_current_user),
):
    note = _own_note(note_id, current_user["sub"])
    db = get_supabase()
    existing_names = _existing_note_names(note["project_id"], exclude_id=note_id)
    unique_name = next_unique_name(body.name, existing_names)
    result = db.table("notes").update({"name": unique_name}).eq("id", note_id).execute()
    row: Any = result.data[0]
    return row


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: str,
    current_user: dict = Depends(get_current_user),
):
    _own_note(note_id, current_user["sub"])
    db = get_supabase()
    db.table("notes").delete().eq("id", note_id).execute()
