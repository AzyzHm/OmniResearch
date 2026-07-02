from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from backend.config.auth import get_current_user
from backend.config.settings import get_settings
from backend.database.chroma_client import (
    add_item_chunks,
    create_chroma_collection,
    delete_chroma_collection,
    delete_item_chunks,
)
from backend.database.db import get_supabase
from backend.models.collection import (
    COLLECTION_TYPE_TO_EXT,
    COLLECTION_TYPE_TO_SOURCE,
    CollectionCreate,
    CollectionItemOut,
    CollectionItemUpdate,
    CollectionOut,
)
from backend.services.embeddings import embed_texts
from backend.services.extraction import extract_pdf, extract_txt
from backend.services.text_processing import chunk_text

router = APIRouter(tags=["Collections"])

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



@router.get("/collections/{collection_id}/items", response_model=list[CollectionItemOut])
async def list_items(
    collection_id: str,
    current_user: dict = Depends(get_current_user),
):
    _own_collection(collection_id, current_user["sub"])
    db = get_supabase()
    result = (
        db.table("collection_items")
        .select("*")
        .eq("collection_id", collection_id)
        .order("created_at", desc=False)
        .execute()
    )
    return result.data


@router.post("/collections/{collection_id}/items", response_model=list[CollectionItemOut])
async def upload_items(
    collection_id: str,
    files: list[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload one or more files into a collection.

    Only 'text' (.txt) and 'documents' (.pdf) collections accept uploads
    right now. Each file is extracted, chunked, embedded via the local
    embeddinggemma model, stored in the collection's Chroma collection
    (raw chunk text + vector), and tracked as a row in collection_items.
    """
    collection = _own_collection(collection_id, current_user["sub"])
    col_type = collection["type"]

    if col_type not in COLLECTION_TYPE_TO_SOURCE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This collection type does not support file uploads yet.",
        )

    expected_ext = COLLECTION_TYPE_TO_EXT[col_type]
    source_type = COLLECTION_TYPE_TO_SOURCE[col_type]

    invalid = [f.filename for f in files if not (f.filename or "").lower().endswith(expected_ext)]
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"These files are not {expected_ext} files: {', '.join(str(n) for n in invalid)}",
        )

    db = get_supabase()
    settings = get_settings()

    results: list[dict] = []

    for upload in files:
        filename = upload.filename or "untitled"
        raw_bytes = await upload.read()

        insert_result = db.table("collection_items").insert({
            "collection_id": collection_id,
            "name": filename,
            "source_type": source_type,
            "status": "processing",
        }).execute()
        item_row: Any = insert_result.data[0]
        item_id = item_row["id"]

        try:
            text = extract_txt(raw_bytes) if source_type == "txt" else extract_pdf(raw_bytes)

            chunks = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
            if not chunks:
                raise ValueError("No extractable text was found in this file.")

            vectors = embed_texts(chunks)

            add_item_chunks(
                collection_id=collection_id,
                item_id=item_id,
                chunks=chunks,
                embeddings=vectors,
                source_name=filename,
            )

            update_result = db.table("collection_items").update({
                "status": "ready",
                "chunk_count": len(chunks),
            }).eq("id", item_id).execute()
            item_row = update_result.data[0]

        except Exception as exc:
            update_result = db.table("collection_items").update({
                "status": "error",
                "error_message": str(exc),
            }).eq("id", item_id).execute()
            item_row = update_result.data[0]

        results.append(item_row)

    return results


@router.patch("/collections/{collection_id}/items/{item_id}", response_model=CollectionItemOut)
async def update_item(
    collection_id: str,
    item_id: str,
    body: CollectionItemUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Toggle whether an item is included as LLM context (is_active)."""
    _own_collection(collection_id, current_user["sub"])
    db = get_supabase()
    result = (
        db.table("collection_items")
        .update({"is_active": body.is_active})
        .eq("id", item_id)
        .eq("collection_id", collection_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found.")
    return result.data[0]


@router.delete(
    "/collections/{collection_id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_item(
    collection_id: str,
    item_id: str,
    current_user: dict = Depends(get_current_user),
):
    _own_collection(collection_id, current_user["sub"])
    delete_item_chunks(collection_id, item_id)
    db = get_supabase()
    db.table("collection_items").delete().eq("id", item_id).eq("collection_id", collection_id).execute()