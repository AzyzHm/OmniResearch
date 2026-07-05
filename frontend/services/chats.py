import json

import requests

from frontend.services.base import _call, _session
from frontend.utils.config import API_BASE, _TIMEOUT


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

    Calls _session directly (rather than going through _call) because it
    needs stream=True and an Accept: text/event-stream header, which the
    shared JSON-oriented _call helper doesn't support.
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
        if not line or not line.startswith("data: "):  # type: ignore
            continue
        payload = line[len("data: "):]
        try:
            event = json.loads(payload)
        except json.JSONDecodeError:
            continue
        yield event