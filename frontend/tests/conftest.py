import os
from typing import Callable, Iterator
from unittest.mock import MagicMock

os.environ.setdefault("API_BASE_URL", "http://fake-api.test")

import pytest


class FakeResponse:
    """Minimal stand-in for requests.Response, just enough for _call()/_call_multipart()."""

    def __init__(self, status_code=200, json_data=None, text="", content=b"1"):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text
        if content is None:
            content = b"" if status_code == 204 else b"1"
        self.content = content
        self.iter_lines: Callable[..., Iterator[str]] = lambda decode_unicode=True: iter([])

    def json(self):
        if self._json_data is None:
            raise ValueError("No JSON data on this fake response")
        return self._json_data


@pytest.fixture()
def mock_call(monkeypatch):
    """
    Patch `_call` inside a given service module and return the MagicMock,
    so tests can assert exactly how it was invoked.

    Usage:
        stub = mock_call(monkeypatch, frontend.services.projects, return_value=[...])
        list_projects("tok")
        stub.assert_called_once_with("GET", "/projects", token="tok")
    """
    def _patch(module, return_value=None, side_effect=None):
        stub = MagicMock(return_value=return_value, side_effect=side_effect)
        monkeypatch.setattr(module, "_call", stub)
        return stub
    return _patch


@pytest.fixture()
def mock_call_multipart(monkeypatch):
    """Same as mock_call, but for `_call_multipart`."""
    def _patch(module, return_value=None, side_effect=None):
        stub = MagicMock(return_value=return_value, side_effect=side_effect)
        monkeypatch.setattr(module, "_call_multipart", stub)
        return stub
    return _patch


@pytest.fixture()
def patched_session_request(monkeypatch):
    """
    Patch the shared `_session.request` method used inside base._call /
    base._call_multipart, returning the MagicMock so tests can configure
    `.return_value` (a FakeResponse) or `.side_effect` (an exception).
    """
    import frontend.services.base as base_mod
    stub = MagicMock()
    monkeypatch.setattr(base_mod._session, "request", stub)
    return stub


@pytest.fixture()
def patched_session_post(monkeypatch):
    """Patch `_session.post`, used directly by chats.send_message_stream."""
    import frontend.services.base as base_mod
    stub = MagicMock()
    monkeypatch.setattr(base_mod._session, "post", stub)
    return stub