import requests
import pytest

import frontend.services.chats as chats
from frontend.tests.conftest import FakeResponse


class TestListChats:
    def test_calls_correct_endpoint(self, mock_call):
        stub = mock_call(chats, return_value=[{"id": "c1", "name": "My Chat"}])
        result = chats.list_chats("tok", "proj-1")
        stub.assert_called_once_with("GET", "/projects/proj-1/chats", token="tok")
        assert result == [{"id": "c1", "name": "My Chat"}]

    def test_none_response_falls_back_to_empty_list(self, mock_call):
        mock_call(chats, return_value=None)
        assert chats.list_chats("tok", "proj-1") == []


class TestCreateChat:
    def test_default_name(self, mock_call):
        stub = mock_call(chats, return_value={"id": "c1", "name": "New Chat"})
        chats.create_chat("tok", "proj-1")
        stub.assert_called_once_with(
            "POST", "/projects/proj-1/chats", token="tok", json={"name": "New Chat"}
        )

    def test_custom_name(self, mock_call):
        stub = mock_call(chats, return_value={"id": "c1", "name": "Custom"})
        chats.create_chat("tok", "proj-1", name="Custom")
        stub.assert_called_once_with(
            "POST", "/projects/proj-1/chats", token="tok", json={"name": "Custom"}
        )


class TestRenameChat:
    def test_calls_correct_endpoint(self, mock_call):
        stub = mock_call(chats, return_value={"id": "c1", "name": "Renamed"})
        chats.rename_chat("tok", "c1", "Renamed")
        stub.assert_called_once_with("PUT", "/chats/c1", token="tok", json={"name": "Renamed"})


class TestDeleteChat:
    def test_calls_correct_endpoint(self, mock_call):
        stub = mock_call(chats, return_value=None)
        chats.delete_chat("tok", "c1")
        stub.assert_called_once_with("DELETE", "/chats/c1", token="tok")


class TestGetMessages:
    def test_calls_correct_endpoint(self, mock_call):
        stub = mock_call(chats, return_value=[{"role": "user", "content": "Hi"}])
        result = chats.get_messages("tok", "c1")
        stub.assert_called_once_with("GET", "/chats/c1/messages", token="tok")
        assert result == [{"role": "user", "content": "Hi"}]

    def test_none_response_falls_back_to_empty_list(self, mock_call):
        mock_call(chats, return_value=None)
        assert chats.get_messages("tok", "c1") == []


class TestSendMessage:
    def test_calls_correct_endpoint(self, mock_call):
        stub = mock_call(chats, return_value={"response": "Hi there!"})
        result = chats.send_message("tok", "c1", "Hello")
        stub.assert_called_once_with(
            "POST", "/chats/c1/message", token="tok", json={"message": "Hello"}
        )
        assert result["response"] == "Hi there!"


def _sse_body(*events: str) -> list:
    """Build the list of lines requests.Response.iter_lines() would yield."""
    lines = []
    for e in events:
        lines.append(f"data: {e}")
        lines.append("")
    return lines


class TestSendMessageStream:
    def test_yields_parsed_events(self, patched_session_post):
        resp = FakeResponse(status_code=200)
        resp.iter_lines = lambda decode_unicode=True: iter(_sse_body(
            '{"type": "node", "node": "router"}',
            '{"type": "done", "answer": "Final answer"}',
        ))
        patched_session_post.return_value = resp

        events = list(chats.send_message_stream("tok", "c1", "Hello"))
        assert events[0] == {"type": "node", "node": "router"}
        assert events[1] == {"type": "done", "answer": "Final answer"}

    def test_ignores_non_data_lines(self, patched_session_post):
        resp = FakeResponse(status_code=200)
        resp.iter_lines = lambda decode_unicode=True: iter([
            ": this is a comment line",
            "",
            'data: {"type": "done", "answer": "ok"}',
        ])
        patched_session_post.return_value = resp

        events = list(chats.send_message_stream("tok", "c1", "Hello"))
        assert events == [{"type": "done", "answer": "ok"}]

    def test_skips_malformed_json(self, patched_session_post):
        resp = FakeResponse(status_code=200)
        resp.iter_lines = lambda decode_unicode=True: iter([
            "data: not valid json",
            'data: {"type": "done", "answer": "ok"}',
        ])
        patched_session_post.return_value = resp

        events = list(chats.send_message_stream("tok", "c1", "Hello"))
        assert events == [{"type": "done", "answer": "ok"}]

    def test_error_status_raises_runtime_error(self, patched_session_post):
        patched_session_post.return_value = FakeResponse(
            status_code=502, json_data={"detail": "RAG error: boom"}
        )
        with pytest.raises(RuntimeError, match="RAG error: boom"):
            list(chats.send_message_stream("tok", "c1", "Hello"))

    def test_connection_error_raises_friendly_message(self, patched_session_post):
        patched_session_post.side_effect = requests.exceptions.ConnectionError()
        with pytest.raises(RuntimeError, match="Cannot reach the API server"):
            list(chats.send_message_stream("tok", "c1", "Hello"))

    def test_timeout_raises_friendly_message(self, patched_session_post):
        patched_session_post.side_effect = requests.exceptions.Timeout()
        with pytest.raises(RuntimeError, match="took too long"):
            list(chats.send_message_stream("tok", "c1", "Hello"))

    def test_sends_correct_headers_and_body(self, patched_session_post):
        resp = FakeResponse(status_code=200)
        resp.iter_lines = lambda decode_unicode=True: iter([])
        patched_session_post.return_value = resp

        list(chats.send_message_stream("tok", "c1", "Hello there"))
        _, kwargs = patched_session_post.call_args
        assert kwargs["headers"]["Authorization"] == "Bearer tok"
        assert kwargs["headers"]["Accept"] == "text/event-stream"
        assert kwargs["json"] == {"message": "Hello there"}
        assert kwargs["stream"] is True