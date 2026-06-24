"""
routes/collections.py – Collection CRUD, mirrored in ChromaDB.

Every collection created in Supabase gets a corresponding ChromaDB collection
keyed by the same UUID.  Deletion removes both.

GET    /projects/{project_id}/collections   → list collections
POST   /projects/{project_id}/collections   → create (Supabase + ChromaDB)
DELETE /collections/{collection_id}         → delete (Supabase + ChromaDB)
"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from backend.config.auth import get_current_user
from backend.database.chroma_client import create_chroma_collection, delete_chroma_collection
from backend.database.db import get_supabase
from backend.models.collection import CollectionCreate, CollectionOut

router = APIRouter(tags=["Collections"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _verify_project_owner(project_id: str, user_id: str) -> None:
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


def _own_collection(collection_id: str, user_id: str) -> dict:
    """Fetch a collection and verify ownership through its project."""
    db = get_supabase()
    result = (
        db.table("collections")
        .select("*, projects(user_id)")
        .eq("id", collection_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found.")
    row: Any = result.data[0]
    project: Any = row.get("projects") or {}
    if project.get("user_id") != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found.")
    return row


# ── List ──────────────────────────────────────────────────────────────────────

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


# ── Create ────────────────────────────────────────────────────────────────────

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

    # 1. Insert metadata into Supabase
    result = db.table("collections").insert(
        {"project_id": project_id, "name": body.name, "type": body.type}
    ).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create collection.")

    row: Any = result.data[0]

    # 2. Mirror in ChromaDB using the Supabase UUID as the collection name
    create_chroma_collection(
        collection_id=row["id"],
        metadata={"name": body.name, "type": body.type, "project_id": project_id},
    )

    return row


# ── Delete ────────────────────────────────────────────────────────────────────

@router.delete("/collections/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(
    collection_id: str,
    current_user: dict = Depends(get_current_user),
):
    _own_collection(collection_id, current_user["sub"])
    db = get_supabase()

    # 1. Remove from ChromaDB first (safe even if it doesn't exist)
    delete_chroma_collection(collection_id)

    # 2. Remove metadata from Supabase
    db.table("collections").delete().eq("id", collection_id).execute()