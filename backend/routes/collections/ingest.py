from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status

from config.auth import get_current_user
from config.settings import get_settings
from database.chroma_client import add_item_chunks
from database.db import get_supabase
from models.collection import ALLOWED_UPLOAD_EXTENSIONS, EXT_TO_SOURCE_TYPE, CollectionItemOut
from models.search import AddSearchResults, AddSearchResultsResponse, ManualUrlAdd
from routes.collections._shared import _existing_urls, _own_collection
from services.embeddings import embed_texts
from services.extraction import count_pdf_pages, count_words, extract_pdf, extract_txt
from services.file_storage import upload_collection_file
from services.text_processing import chunk_text
from services.web_fetch import fetch_url_markdown

router = APIRouter()


def _process_upload_item(
    collection_id: str,
    item_id: str,
    filename: str,
    source_type: str,
    raw_bytes: bytes,
) -> None:
    """Background task: extract, chunk, embed, and store a single uploaded file."""
    db = get_supabase()
    settings = get_settings()
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

        page_count = count_pdf_pages(raw_bytes) if source_type == "pdf" else None
        word_count = count_words(text) if source_type == "txt" else None

        storage_path = f"{collection_id}/{item_id}/{filename}"
        content_type = "application/pdf" if source_type == "pdf" else "text/plain"
        stored_path: str | None = storage_path
        try:
            upload_collection_file(storage_path, raw_bytes, content_type)
        except Exception as exc:
            print(f"Warning: failed to store original file for item {item_id!r}: {exc}")
            stored_path = None

        db.table("collection_items").update(
            {
                "status": "ready",
                "chunk_count": len(chunks),
                "page_count": page_count,
                "word_count": word_count,
                "storage_path": stored_path,
            }
        ).eq("id", item_id).execute()

    except Exception as exc:
        db.table("collection_items").update(
            {
                "status": "error",
                "error_message": str(exc),
            }
        ).eq("id", item_id).execute()


def _process_url_item(collection_id: str, item_id: str, url: str) -> None:
    """Background task: fetch (Jina), chunk, embed, and store a manually-added URL."""
    db = get_supabase()
    settings = get_settings()
    try:
        text = fetch_url_markdown(url)
        chunks = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
        if not chunks:
            raise ValueError("No extractable content was found at this URL.")

        vectors = embed_texts(chunks)
        add_item_chunks(collection_id, item_id, chunks, vectors, source_name=url)

        db.table("collection_items").update(
            {
                "status": "ready",
                "chunk_count": len(chunks),
            }
        ).eq("id", item_id).execute()

    except Exception as exc:
        db.table("collection_items").update(
            {
                "status": "error",
                "error_message": str(exc),
            }
        ).eq("id", item_id).execute()


def _process_search_result_item(collection_id: str, item_id: str, url: str, content: str) -> None:
    """Background task: chunk, embed, and store a URL selected from a web search.
    Content is the engine-provided snippet already returned by Tavily/Exa — no
    network fetch here, just chunking + embedding."""
    db = get_supabase()
    settings = get_settings()
    try:
        chunks = chunk_text(content, settings.chunk_size, settings.chunk_overlap)
        if not chunks:
            raise ValueError("Selected result has no content to store.")

        vectors = embed_texts(chunks)
        add_item_chunks(collection_id, item_id, chunks, vectors, source_name=url)

        db.table("collection_items").update(
            {
                "status": "ready",
                "chunk_count": len(chunks),
            }
        ).eq("id", item_id).execute()

    except Exception as exc:
        db.table("collection_items").update(
            {
                "status": "error",
                "error_message": str(exc),
            }
        ).eq("id", item_id).execute()


@router.post("/collections/{collection_id}/items", response_model=list[CollectionItemOut])
async def upload_items(
    collection_id: str,
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload one or more files into a collection.

    Every collection accepts a mix of PDF and TXT files — the source type is
    derived per-file from its own extension, not from a collection-wide
    setting. Each file is inserted as a "processing" row immediately;
    extraction, chunking, and embedding happen afterward as a background
    task, so this endpoint returns right away instead of blocking on the
    full pipeline.
    """
    _own_collection(collection_id, current_user["sub"])

    invalid = [f.filename for f in files if not (f.filename or "").lower().endswith(ALLOWED_UPLOAD_EXTENSIONS)]
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported file type for: {', '.join(str(n) for n in invalid)}. "
                f"Only {' and '.join(ALLOWED_UPLOAD_EXTENSIONS)} files are supported."
            ),
        )

    db = get_supabase()
    results: list[dict] = []

    for upload in files:
        filename = upload.filename or "untitled"
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        source_type = EXT_TO_SOURCE_TYPE[ext]
        raw_bytes = await upload.read()

        insert_result = (
            db.table("collection_items")
            .insert(
                {
                    "collection_id": collection_id,
                    "name": filename,
                    "source_type": source_type,
                    "status": "processing",
                }
            )
            .execute()
        )
        item_row: Any = insert_result.data[0]
        item_id = item_row["id"]

        background_tasks.add_task(
            _process_upload_item,
            collection_id,
            item_id,
            filename,
            source_type,
            raw_bytes,
        )
        results.append(item_row)

    return results


@router.post("/collections/{collection_id}/items/url", response_model=CollectionItemOut)
async def add_url_item(
    collection_id: str,
    body: ManualUrlAdd,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """Manually add a single URL to any collection. The item row is inserted
    as "processing" and returned immediately; the Jina fetch + chunk + embed
    happens afterward as a background task."""
    _own_collection(collection_id, current_user["sub"])

    url = body.url.strip()
    if url in _existing_urls(collection_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This URL has already been added to this collection.",
        )

    db = get_supabase()

    insert_result = (
        db.table("collection_items")
        .insert(
            {
                "collection_id": collection_id,
                "name": url,
                "source_type": "url",
                "status": "processing",
            }
        )
        .execute()
    )
    item_row: Any = insert_result.data[0]
    item_id = item_row["id"]

    background_tasks.add_task(_process_url_item, collection_id, item_id, url)

    return item_row


@router.post(
    "/collections/{collection_id}/items/from-search",
    response_model=AddSearchResultsResponse,
)
async def add_search_result_items(
    collection_id: str,
    body: AddSearchResults,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """
    Bulk-add URLs selected from a Tavily/Exa search modal, into any collection.

    Every non-duplicate item is inserted as "processing" and the response is
    returned immediately, so the frontend can close the search modal right
    away. Content is stored exactly as returned by the search engine (snippet
    / highlights) — no re-fetch, just chunking + embedding, each done as a
    background task per item. URLs already present in the collection are
    skipped rather than erroring the whole batch.
    """
    _own_collection(collection_id, current_user["sub"])

    db = get_supabase()
    existing = _existing_urls(collection_id)

    added: list[dict] = []
    skipped: list[str] = []

    for result_item in body.items:
        url = result_item.url.strip()
        if not url or url in existing:
            skipped.append(url)
            continue
        existing.add(url)

        insert_result = (
            db.table("collection_items")
            .insert(
                {
                    "collection_id": collection_id,
                    "name": url,
                    "source_type": "url",
                    "status": "processing",
                }
            )
            .execute()
        )
        item_row: Any = insert_result.data[0]
        item_id = item_row["id"]

        background_tasks.add_task(
            _process_search_result_item,
            collection_id,
            item_id,
            url,
            result_item.content.strip(),
        )
        added.append(item_row)

    return {"added": added, "skipped": skipped}
