from fastapi import APIRouter, Depends, HTTPException, status

from backend.config.auth import get_current_user
from backend.database.chroma_client import delete_item_chunks
from backend.database.db import get_supabase
from backend.models.collection import BulkItemsUpdateRequest, CollectionItemOut, CollectionItemUpdate
from backend.routes.collections._shared import _own_collection

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