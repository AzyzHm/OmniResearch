from frontend.services.base import _call, _call_multipart


def list_collections(token: str, project_id: str) -> list:
    return _call("GET", f"/projects/{project_id}/collections", token=token) or []


def create_collection(token: str, project_id: str, name: str, col_type: str) -> dict:
    return _call(
        "POST",
        f"/projects/{project_id}/collections",
        token=token,
        json={"name": name, "type": col_type},
    )


def delete_collection(token: str, collection_id: str) -> None:
    _call("DELETE", f"/collections/{collection_id}", token=token)


def list_collection_items(token: str, collection_id: str) -> list:
    return _call("GET", f"/collections/{collection_id}/items", token=token) or []


def upload_collection_items(
    token: str,
    collection_id: str,
    uploaded_files: list,
) -> list:
    """
    uploaded_files: list of Streamlit UploadedFile objects
    (has .name, .type, and .getvalue()).
    """
    files = [
        ("files", (f.name, f.getvalue(), f.type or "application/octet-stream"))
        for f in uploaded_files
    ]
    return _call_multipart(
        "POST",
        f"/collections/{collection_id}/items",
        token=token,
        files=files,
    ) or []


def toggle_collection_item(token: str, collection_id: str, item_id: str, is_active: bool) -> dict:
    return _call(
        "PATCH",
        f"/collections/{collection_id}/items/{item_id}",
        token=token,
        json={"is_active": is_active},
    )


def bulk_update_collection_items(token: str, collection_id: str, updates: list[dict]) -> list:
    """updates: list of {"item_id": ..., "is_active": ...} dicts."""
    return _call(
        "PATCH",
        f"/collections/{collection_id}/items/bulk",
        token=token,
        json={"updates": updates},
    ) or []


def delete_collection_item(token: str, collection_id: str, item_id: str) -> None:
    _call("DELETE", f"/collections/{collection_id}/items/{item_id}", token=token)


def add_url_item(token: str, collection_id: str, url: str) -> dict:
    return _call(
        "POST",
        f"/collections/{collection_id}/items/url",
        token=token,
        json={"url": url},
    )