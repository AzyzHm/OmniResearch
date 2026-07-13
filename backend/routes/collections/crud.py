from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from backend.config.auth import get_current_user
from backend.database.chroma_client import create_chroma_collection, delete_chroma_collection
from backend.database.db import get_supabase
from backend.models.collection import CollectionCreate, CollectionOut
from backend.routes.collections._shared import _own_collection, _verify_project_owner

router = APIRouter()


@router.get("/projects/{project_id}/collections", response_model=list[CollectionOut])
async def list_collections(
    project_id: str,
    current_user: dict = Depends(get_current_user),
):
    _verify_project_owner(project_id, current_user["sub"])
    db = get_supabase()
    result = (
        db.table("collections")
        .select("id, project_id, name, type, created_at")
        .eq("project_id", project_id)
        .order("created_at", desc=False)
        .execute()
    )
    return result.data

@router.post(
    "/projects/{project_id}/collections",
    response_model=CollectionOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_collection(
    project_id: str,
    body: CollectionCreate,
    current_user: dict = Depends(get_current_user),
):
    _verify_project_owner(project_id, current_user["sub"])
    db = get_supabase()

    result = db.table("collections").insert(
        {"project_id": project_id, "name": body.name, "type": body.type}
    ).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create collection.")

    row: Any = result.data[0]

    create_chroma_collection(
        collection_id=row["id"],
        metadata={"name": body.name, "type": body.type, "project_id": project_id},
    )

    return row


@router.delete("/collections/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(
    collection_id: str,
    current_user: dict = Depends(get_current_user),
):
    _own_collection(collection_id, current_user["sub"])
    db = get_supabase()

    delete_chroma_collection(collection_id)

    db.table("collections").delete().eq("id", collection_id).execute()