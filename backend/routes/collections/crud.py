from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from config.auth import get_current_user
from database.chroma_client import create_chroma_collection, delete_chroma_collection
from database.db import get_supabase
from models.collection import CollectionCreate, CollectionOut
from routes.collections._shared import _own_collection, _verify_project_owner
from utils.naming import next_unique_name

router = APIRouter()


def _existing_collection_names(project_id: str) -> list[str]:
    """Names of the project's existing collections, used to silently dedupe on create."""
    db = get_supabase()
    result = db.table("collections").select("id, name").eq("project_id", project_id).execute()
    return [row["name"] for row in result.data]


@router.get("/projects/{project_id}/collections", response_model=list[CollectionOut])
async def list_collections(
    project_id: str,
    current_user: dict = Depends(get_current_user),
):
    _verify_project_owner(project_id, current_user["sub"])
    db = get_supabase()
    result = (
        db.table("collections")
        .select("id, project_id, name, created_at")
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

    existing_names = _existing_collection_names(project_id)
    unique_name = next_unique_name(body.name, existing_names)

    result = db.table("collections").insert({"project_id": project_id, "name": unique_name}).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create collection.")

    row: Any = result.data[0]

    create_chroma_collection(
        collection_id=row["id"],
        metadata={"name": unique_name, "project_id": project_id},
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
