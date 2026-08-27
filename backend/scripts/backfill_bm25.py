from backend.database.chroma_client import get_chroma
from backend.database.db import get_supabase
from backend.services.bm25 import bm25_sparse_vectors, sparse_vector_to_metadata


def backfill_collection(collection_id: str) -> int:
    """Backfill one Chroma collection. Returns the number of chunks updated."""
    client = get_chroma()
    try:
        collection = client.get_collection(name=collection_id)
    except Exception as exc:
        print(f"  ! skipping {collection_id}: {exc}")
        return 0

    existing = collection.get(include=["documents", "metadatas"])
    ids = existing.get("ids") or []
    documents = existing.get("documents") or []
    metadatas = existing.get("metadatas") or []

    if not ids:
        return 0

    sparse_vectors = bm25_sparse_vectors(documents)
    updated_metadatas = [
        {**(meta or {}), **sparse_vector_to_metadata(sv)}
        for meta, sv in zip(metadatas, sparse_vectors)
    ]

    collection.update(ids=ids, metadatas=updated_metadatas)
    return len(ids)


def main() -> None:
    db = get_supabase()
    result = db.table("collections").select("id, name").execute()
    collections = result.data or []

    if not collections:
        print("No collections found — nothing to backfill.")
        return

    total = 0
    for row in collections:
        count = backfill_collection(row["id"]) # type: ignore
        total += count
        print(f"  {row['name']} ({row['id']}): {count} chunk(s) updated") # type: ignore

    print(f"\nDone — {total} chunk(s) backfilled with BM25 vectors across {len(collections)} collection(s).")


if __name__ == "__main__":
    main()