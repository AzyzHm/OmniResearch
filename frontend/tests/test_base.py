import pytest
import requests

from frontend.tests.conftest import FakeResponse
from frontend.services.base import _call, _call_multipart


class TestCallSuccess:
    def test_returns_parsed_json(self, patched_session_request):
        patched_session_request.return_value = FakeResponse(status_code=200, json_data={"ok": True})
        result = _call("GET", "/projects")
        assert result == {"ok": True}

    def test_204_returns_none(self, patched_session_request):
        patched_session_request.return_value = FakeResponse(status_code=204, content=b"")
        result = _call("DELETE", "/projects/1")
        assert result is None

    def test_empty_content_returns_none(self, patched_session_request):
        patched_session_request.return_value = FakeResponse(status_code=200, content=b"")
        result = _call("GET", "/health")
        assert result is None

    def test_url_built_from_api_base_and_path(self, patched_session_request):
        patched_session_request.return_value = FakeResponse(json_data={})
        _call("GET", "/projects")
        args, kwargs = patched_session_request.call_args
        assert args[0] == "GET"
        assert args[1] == "http://fake-api.test/projects"

    def test_json_body_forwarded(self, patched_session_request):
        patched_session_request.return_value = FakeResponse(json_data={})
        _call("POST", "/projects", json={"name": "New Project"})
        _, kwargs = patched_session_request.call_args
        assert kwargs["json"] == {"name": "New Project"}

    def test_params_forwarded(self, patched_session_request):
        patched_session_request.return_value = FakeResponse(json_data={})
        _call("GET", "/admin/logs", params={"limit": 50, "offset": 0})
        _, kwargs = patched_session_request.call_args
        assert kwargs["params"] == {"limit": 50, "offset": 0}


class TestCallAuthHeader:
    def test_token_adds_authorization_header(self, patched_session_request):
        patched_session_request.return_value = FakeResponse(json_data={})
        _call("GET", "/projects", token="my-token")
        _, kwargs = patched_session_request.call_args
        assert kwargs["headers"]["Authorization"] == "Bearer my-token"

    def test_no_token_omits_authorization_header(self, patched_session_request):
        patched_session_request.return_value = FakeResponse(json_data={})
        _call("POST", "/auth/login", json={"username": "a", "password": "b"})
        _, kwargs = patched_session_request.call_args
        assert "Authorization" not in kwargs["headers"]

    def test_content_type_and_accept_headers_set(self, patched_session_request):
        patched_session_request.return_value = FakeResponse(json_data={})
        _call("GET", "/projects")
        _, kwargs = patched_session_request.call_args
        assert kwargs["headers"]["Content-Type"] == "application/json"
        assert kwargs["headers"]["Accept"] == "application/json"


class TestCallErrorStatusCodes:
    def test_400_raises_runtime_error_with_json_detail(self, patched_session_request):
        patched_session_request.return_value = FakeResponse(
            status_code=400, json_data={"detail": "Bad request"}
        )
        with pytest.raises(RuntimeError, match="Bad request"):
            _call("POST", "/projects", json={})

    def test_404_raises_runtime_error(self, patched_session_request):
        patched_session_request.return_value = FakeResponse(
            status_code=404, json_data={"detail": "Not found"}
        )
        with pytest.raises(RuntimeError, match="Not found"):
            _call("GET", "/projects/missing")

    def test_500_with_non_json_body_falls_back_to_text(self, patched_session_request):
        patched_session_request.return_value = FakeResponse(
            status_code=500, json_data=None, text="Internal Server Error"
        )
        with pytest.raises(RuntimeError, match="Internal Server Error"):
            _call("GET", "/projects")


class TestCallNetworkErrors:
    def test_connection_error_raises_friendly_message(self, patched_session_request):
        patched_session_request.side_effect = requests.exceptions.ConnectionError()
        with pytest.raises(RuntimeError, match="Cannot reach the API server"):
            _call("GET", "/projects")

    def test_timeout_raises_friendly_message(self, patched_session_request):
        patched_session_request.side_effect = requests.exceptions.Timeout()
        with pytest.raises(RuntimeError, match="took too long"):
            _call("GET", "/projects")

    def test_generic_request_exception_raises_wrapped_message(self, patched_session_request):
        patched_session_request.side_effect = requests.exceptions.RequestException("boom")
        with pytest.raises(RuntimeError, match="Network error"):
            _call("GET", "/projects")


class TestCallMultipart:
    def test_returns_parsed_json(self, patched_session_request):
        patched_session_request.return_value = FakeResponse(json_data=[{"id": "item-1"}])
        result = _call_multipart(
            "POST", "/collections/col-1/items",
            files=[("files", ("a.txt", b"hello", "text/plain"))],
        )
        assert result == [{"id": "item-1"}]

    def test_content_type_header_not_set(self, patched_session_request):
        """requests must generate its own multipart boundary; Content-Type must be absent."""
        patched_session_request.return_value = FakeResponse(json_data=[])
        _call_multipart(
            "POST", "/collections/col-1/items",
            files=[("files", ("a.txt", b"hello", "text/plain"))],
        )
        _, kwargs = patched_session_request.call_args
        assert "Content-Type" not in kwargs["headers"]

    def test_files_forwarded(self, patched_session_request):
        patched_session_request.return_value = FakeResponse(json_data=[])
        files = [("files", ("a.txt", b"hello", "text/plain"))]
        _call_multipart("POST", "/collections/col-1/items", files=files)
        _, kwargs = patched_session_request.call_args
        assert kwargs["files"] == files

    def test_token_adds_authorization_header(self, patched_session_request):
        patched_session_request.return_value = FakeResponse(json_data=[])
        _call_multipart(
            "POST", "/collections/col-1/items",
            token="my-token",
            files=[("files", ("a.txt", b"hello", "text/plain"))],
        )
        _, kwargs = patched_session_request.call_args
        assert kwargs["headers"]["Authorization"] == "Bearer my-token"

    def test_error_status_raises_runtime_error(self, patched_session_request):
        patched_session_request.return_value = FakeResponse(
            status_code=413, json_data={"detail": "File too large"}
        )
        with pytest.raises(RuntimeError, match="File too large"):
            _call_multipart(
                "POST", "/collections/col-1/items",
                files=[("files", ("a.txt", b"hello", "text/plain"))],
            )

    def test_connection_error_raises_friendly_message(self, patched_session_request):
        patched_session_request.side_effect = requests.exceptions.ConnectionError()
        with pytest.raises(RuntimeError, match="Cannot reach the API server"):
            _call_multipart(
                "POST", "/collections/col-1/items",
                files=[("files", ("a.txt", b"hello", "text/plain"))],
            )