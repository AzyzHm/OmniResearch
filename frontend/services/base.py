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