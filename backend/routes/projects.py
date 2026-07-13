from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status

from backend.config.auth import get_current_user
from backend.database.db import get_supabase
from backend.models.project import ProjectCreate, ProjectOut, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["Projects"])


def _own_project(project_id: str, user_id: str) -> dict:
    """Fetch a project and verify it belongs to the current user."""
    db = get_supabase()
    result = (
        db.table("projects")
        .select("*")
        .eq("id", project_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    row: Any = result.data[0]
    return row

@router.get("", response_model=list[ProjectOut])
async def list_projects(current_user: dict = Depends(get_current_user)):
    """Return all projects that belong to the authenticated user."""
    db = get_supabase()
    result = (
        db.table("projects")
        .select("*")
        .eq("user_id", current_user["sub"])
        .order("updated_at", desc=True)
        .execute()
    )
    return result.data

@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    current_user: dict = Depends(get_current_user),
):
    db = get_supabase()
    result = db.table("projects").insert(
        {"user_id": current_user["sub"], "name": body.name}
    ).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create project.")
    row: Any = result.data[0]
    return row

@router.put("/{project_id}", response_model=ProjectOut)
async def rename_project(
    project_id: str,
    body: ProjectUpdate,
    current_user: dict = Depends(get_current_user),
):
    _own_project(project_id, current_user["sub"])
    db = get_supabase()
    result = (
        db.table("projects")
        .update({"name": body.name})
        .eq("id", project_id)
        .execute()
    )
    row: Any = result.data[0]
    return row


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    current_user: dict = Depends(get_current_user),
):
    _own_project(project_id, current_user["sub"])
    db = get_supabase()
    db.table("projects").delete().eq("id", project_id).execute()