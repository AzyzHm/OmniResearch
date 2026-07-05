from __future__ import annotations

import json
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from frontend.utils.config import API_BASE, _TIMEOUT


def _build_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.3,
        status_forcelist=[502, 503, 504],
        allowed_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


_session = _build_session()


def _call(
    method: str,
    path: str,
    *,
    token: str | None = None,
    json: dict | None = None,
    params: dict | None = None,
) -> Any:
    headers: dict[str, str] = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        resp = _session.request(
            method,
            f"{API_BASE}{path}",
            headers=headers,
            json=json,
            params=params,
            timeout=_TIMEOUT,
        )
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            f"Cannot reach the API server at {API_BASE}. "
            "Make sure the FastAPI backend is running."
        )
    except requests.exceptions.Timeout:
        raise RuntimeError("The API server took too long to respond. Please try again.")
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"Network error: {exc}")

    if resp.status_code >= 400:
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        raise RuntimeError(detail)

    if resp.status_code == 204 or not resp.content:
        return None

    return resp.json()


def _call_multipart(
    method: str,
    path: str,
    *,
    token: str | None = None,
    files: list[tuple[str, tuple[str, bytes, str]]],
) -> Any:
    """
    Like _call, but for multipart/form-data uploads. The Content-Type header
    is intentionally NOT set — requests generates the correct multipart
    boundary itself when given the `files` argument.
    """
    headers: dict[str, str] = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        resp = _session.request(
            method,
            f"{API_BASE}{path}",
            headers=headers,
            files=files,
            timeout=_TIMEOUT,
        )
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            f"Cannot reach the API server at {API_BASE}. "
            "Make sure the FastAPI backend is running."
        )
    except requests.exceptions.Timeout:
        raise RuntimeError("The API server took too long to respond. Please try again.")
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"Network error: {exc}")

    if resp.status_code >= 400:
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        raise RuntimeError(detail)

    if resp.status_code == 204 or not resp.content:
        return None

    return resp.json()

def register(username: str, password: str) -> dict:
    return _call("POST", "/auth/register", json={"username": username, "password": password})


def login(username: str, password: str) -> dict:
    return _call("POST", "/auth/login", json={"username": username, "password": password})


def list_projects(token: str) -> list:
    return _call("GET", "/projects", token=token) or []


def create_project(token: str, name: str) -> dict:
    return _call("POST", "/projects", token=token, json={"name": name})


def rename_project(token: str, project_id: str, name: str) -> dict:
    return _call("PUT", f"/projects/{project_id}", token=token, json={"name": name})


def delete_project(token: str, project_id: str) -> None:
    _call("DELETE", f"/projects/{project_id}", token=token)


def list_chats(token: str, project_id: str) -> list:
    return _call("GET", f"/projects/{project_id}/chats", token=token) or []


def create_chat(token: str, project_id: str, name: str = "New Chat") -> dict:
    return _call("POST", f"/projects/{project_id}/chats", token=token, json={"name": name})


def rename_chat(token: str, chat_id: str, name: str) -> dict:
    return _call("PUT", f"/chats/{chat_id}", token=token, json={"name": name})


def delete_chat(token: str, chat_id: str) -> None:
    _call("DELETE", f"/chats/{chat_id}", token=token)


def get_messages(token: str, chat_id: str) -> list:
    """Fetch persisted messages for a chat (oldest first)."""
    return _call("GET", f"/chats/{chat_id}/messages", token=token) or []


def send_message(token: str, chat_id: str, message: str) -> dict:
    """Send a message; backend fetches context and calls Gemini. (Non-streaming fallback.)"""
    return _call(
        "POST",
        f"/chats/{chat_id}/message",
        token=token,
        json={"message": message},
    )


def send_message_stream(token: str, chat_id: str, message: str):
    """
    Yields events from the streaming RAG endpoint as each graph node finishes:
      {"type": "node", "node": "router"}
      {"type": "done", "answer": "..."}
      {"type": "error", "detail": "..."}

    Uses requests' streaming mode: with stream=True, the timeout applies per
    chunk received rather than to the whole response, so a multi-step RAG
    run doesn't get killed by _TIMEOUT just because it takes longer overall.
    """
    headers: dict[str, str] = {"Content-Type": "application/json", "Accept": "text/event-stream"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        resp = _session.post(
            f"{API_BASE}/chats/{chat_id}/message/stream",
            headers=headers,
            json={"message": message},
            stream=True,
            timeout=_TIMEOUT,
        )
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            f"Cannot reach the API server at {API_BASE}. "
            "Make sure the FastAPI backend is running."
        )
    except requests.exceptions.Timeout:
        raise RuntimeError("The API server took too long to respond. Please try again.")
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"Network error: {exc}")

    if resp.status_code >= 400:
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        raise RuntimeError(detail)

    for line in resp.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data: "): # type: ignore
            continue
        payload = line[len("data: "):]
        try:
            event = json.loads(payload)
        except json.JSONDecodeError:
            continue
        yield event

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


def search_web(token: str, engine: str, query: str, num_results: int = 10, search_depth: str = "basic") -> list:
    result = _call(
        "POST",
        "/search/web",
        token=token,
        json={
            "engine": engine,
            "query": query,
            "num_results": num_results,
            "search_depth": search_depth,
        },
    )
    return (result or {}).get("results", [])


def add_search_result_items(token: str, collection_id: str, items: list) -> dict:
    """items: list of {"url": ..., "title": ..., "content": ...} dicts."""
    return _call(
        "POST",
        f"/collections/{collection_id}/items/from-search",
        token=token,
        json={"items": items},
    )


def admin_list_users(token: str, pending_only: bool = False) -> dict:
    return _call("GET", "/admin/users", token=token, params={"pending_only": pending_only})


def admin_approve_user(token: str, user_id: str) -> dict:
    return _call("PUT", f"/admin/users/{user_id}/approve", token=token)


def admin_change_role(token: str, user_id: str, new_role: str) -> dict:
    return _call("PUT", f"/admin/users/{user_id}/role", token=token, params={"new_role": new_role})


def admin_delete_user(token: str, user_id: str) -> dict:
    return _call("DELETE", f"/admin/users/{user_id}", token=token)


def admin_get_logs(token: str, limit: int = 100, offset: int = 0, username: str = "") -> dict:
    params: dict = {"limit": limit, "offset": offset}
    if username:
        params["username"] = username
    return _call("GET", "/admin/logs", token=token, params=params)


def admin_get_stats(token: str) -> dict:
    return _call("GET", "/admin/stats", token=token)


def admin_get_llm_usage(token: str) -> dict:
    return _call("GET", "/admin/usage/llm", token=token)


def admin_get_search_usage(token: str) -> dict:
    return _call("GET", "/admin/usage/search", token=token)