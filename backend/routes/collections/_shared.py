from typing import Any

from fastapi import HTTPException, status

from backend.database.db import get_supabase


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


def _existing_urls(collection_id: str) -> set[str]:
    """URLs already stored as items in this collection (used to reject duplicates)."""
    db = get_supabase()
    result = (
        db.table("collection_items")
        .select("name")
        .eq("collection_id", collection_id)
        .eq("source_type", "url")
        .execute()
    )
    return {row["name"] for row in result.data} # type: ignore