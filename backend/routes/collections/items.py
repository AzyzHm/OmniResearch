from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response

from config.auth import get_current_user
from database.chroma_client import delete_item_chunks
from database.db import get_supabase
from models.collection import BulkItemsUpdateRequest, CollectionItemOut, CollectionItemUpdate
from routes.collections._shared import _own_collection
from services.file_storage import delete_collection_file, download_collection_file

router = APIRouter()


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


@router.patch("/collections/{collection_id}/items/bulk", response_model=list[CollectionItemOut])
async def bulk_update_items(
    collection_id: str,
    body: BulkItemsUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Apply many is_active changes in a single request. Used by the collections
    panel's "Save Changes" button, so toggling several checkboxes only ever
    triggers one API call instead of one per click.
    """
    _own_collection(collection_id, current_user["sub"])
    db = get_supabase()

    results: list[dict] = []
    for update in body.updates:
        result = (
            db.table("collection_items")
            .update({"is_active": update.is_active})
            .eq("id", update.item_id)
            .eq("collection_id", collection_id)
            .execute()
        )
        if result.data:
            results.append(result.data[0]) # type: ignore

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


@router.get("/collections/{collection_id}/items/{item_id}/content")
async def get_item_content(
    collection_id: str,
    item_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Stream a PDF/TXT item's original file so the frontend can preview it in
    a modal — the actual PDF (rendered by the browser) or the exact original
    text, not a reconstruction from RAG chunks. URL items have nothing to
    serve here; the frontend just opens those in a new tab instead.
    """
    _own_collection(collection_id, current_user["sub"])
    db = get_supabase()
    result = (
        db.table("collection_items")
        .select("*")
        .eq("id", item_id)
        .eq("collection_id", collection_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found.")
    item: Any = result.data[0]

    if item["source_type"] not in ("pdf", "txt"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This item type has no viewable content.",
        )
    if not item.get("storage_path"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No stored file for this item. Try re-uploading it.",
        )

    try:
        raw_bytes = download_collection_file(item["storage_path"])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not retrieve the file from storage.",
        )

    media_type = "application/pdf" if item["source_type"] == "pdf" else "text/plain; charset=utf-8"
    return Response(
        content=raw_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'inline; filename="{item["name"]}"'},
    )


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
    db = get_supabase()

    existing = (
        db.table("collection_items")
        .select("storage_path")
        .eq("id", item_id)
        .eq("collection_id", collection_id)
        .execute()
    )

    delete_item_chunks(collection_id, item_id)
    db.table("collection_items").delete().eq("id", item_id).eq("collection_id", collection_id).execute()

    storage_path = existing.data[0].get("storage_path") if existing.data else None #type: ignore
    if storage_path:
        delete_collection_file(storage_path) #type: ignore