from __future__ import annotations

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
        allowed_methods=["GET", "POST", "PUT", "DELETE"],
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


def send_message(token: str, chat_id: str, message: str, history: list[dict]) -> dict:
    return _call(
        "POST",
        f"/chats/{chat_id}/message",
        token=token,
        json={"message": message, "history": history},
    )


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