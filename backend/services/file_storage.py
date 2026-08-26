from config.settings import get_settings
from database.db import get_supabase


def upload_collection_file(path: str, data: bytes, content_type: str) -> None:
    """Upload (or overwrite) a file's raw bytes at `path` in the bucket."""
    db = get_supabase()
    settings = get_settings()
    db.storage.from_(settings.collection_files_bucket).upload(
        path,
        data,
        {"content-type": content_type, "upsert": "true"},
    )


def download_collection_file(path: str) -> bytes:
    """Download a file's raw bytes from `path` in the bucket."""
    db = get_supabase()
    settings = get_settings()
    return db.storage.from_(settings.collection_files_bucket).download(path)


def delete_collection_file(path: str) -> None:
    """Delete a file from the bucket. Best-effort: a storage hiccup here
    should never block the item's DB row from being deleted."""
    db = get_supabase()
    settings = get_settings()
    try:
        db.storage.from_(settings.collection_files_bucket).remove([path])
    except Exception as exc:
        print(f"Warning: failed to delete storage object {path!r}: {exc}")
