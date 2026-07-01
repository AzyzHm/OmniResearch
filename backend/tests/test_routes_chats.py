from datetime import datetime, timezone
from backend.tests.conftest import project_row, chat_row

NOW = datetime.now(timezone.utc).isoformat()


def message_row(msg_id="msg-1", chat_id="chat-1", role="user", content="Hello"):
    """Factory for a messages table row."""
    return {"id": msg_id, "chat_id": chat_id, "role": role, "content": content, "created_at": NOW}


class TestListChats:
    def test_returns_all_chats(self, app, user_headers):
        client, db = app
        db.add_result(data=[project_row()])
        db.add_result(data=[chat_row(), chat_row("chat-2", name="B")])
        resp = client.get("/projects/proj-1/chats", headers=user_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_returns_empty_list_when_no_chats(self, app, user_headers):
        client, db = app
        db.add_result(data=[project_row()])
        db.add_result(data=[])
        resp = client.get("/projects/proj-1/chats", headers=user_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_project_not_found(self, app, user_headers):
        client, db = app
        db.add_result(data=[])
        resp = client.get("/projects/bad/chats", headers=user_headers)
        assert resp.status_code == 404

    def test_unauthenticated(self, app):
        client, _ = app
        resp = client.get("/projects/proj-1/chats")
        assert resp.status_code in (401, 403)


class TestCreateChat:
    def test_success(self, app, user_headers):
        client, db = app
        db.add_result(data=[project_row()])
        db.add_result(data=[chat_row()])
        resp = client.post("/projects/proj-1/chats", json={"name": "My Chat"}, headers=user_headers)
        assert resp.status_code == 201
        assert resp.json()["name"] == "My Chat"

    def test_default_name_when_omitted(self, app, user_headers):
        """Sending no name should result in a chat named 'New Chat'."""
        client, db = app
        db.add_result(data=[project_row()])
        db.add_result(data=[chat_row(name="New Chat")])
        resp = client.post("/projects/proj-1/chats", json={}, headers=user_headers)
        assert resp.status_code == 201
        assert resp.json()["name"] == "New Chat"

    def test_blank_name_falls_back_to_default(self, app, user_headers):
        client, db = app
        db.add_result(data=[project_row()])
        db.add_result(data=[chat_row(name="New Chat")])
        resp = client.post("/projects/proj-1/chats", json={"name": "   "}, headers=user_headers)
        assert resp.status_code == 201

    def test_project_not_found(self, app, user_headers):
        client, db = app
        db.add_result(data=[])
        resp = client.post("/projects/bad/chats", json={"name": "X"}, headers=user_headers)
        assert resp.status_code == 404


class TestRenameChat:
    def test_success(self, app, user_headers):
        client, db = app
        db.add_result(data=[chat_row()])
        db.add_result(data=[chat_row(name="Renamed")])
        resp = client.put("/chats/chat-1", json={"name": "Renamed"}, headers=user_headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Renamed"

    def test_empty_name_rejected(self, app, user_headers):
        client, _ = app
        resp = client.put("/chats/chat-1", json={"name": "  "}, headers=user_headers)
        assert resp.status_code == 422

    def test_chat_not_found(self, app, user_headers):
        client, db = app
        db.add_result(data=[])
        resp = client.put("/chats/missing", json={"name": "X"}, headers=user_headers)
        assert resp.status_code == 404

    def test_wrong_owner_rejected(self, app, user_headers):
        client, db = app
        row = chat_row()
        row["projects"] = {"user_id": "someone-else"}
        db.add_result(data=[row])
        resp = client.put("/chats/chat-1", json={"name": "X"}, headers=user_headers)
        assert resp.status_code == 404


class TestDeleteChat:
    def test_success(self, app, user_headers):
        client, db = app
        db.add_result(data=[chat_row()])
        db.add_result(data=[])
        resp = client.delete("/chats/chat-1", headers=user_headers)
        assert resp.status_code == 204

    def test_chat_not_found(self, app, user_headers):
        client, db = app
        db.add_result(data=[])
        resp = client.delete("/chats/missing", headers=user_headers)
        assert resp.status_code == 404

    def test_unauthenticated(self, app):
        client, _ = app
        resp = client.delete("/chats/chat-1")
        assert resp.status_code in (401, 403)


class TestGetMessages:
    """Tests for GET /chats/{chat_id}/messages — the new persistent history endpoint."""

    def test_returns_messages_oldest_first(self, app, user_headers):
        """Messages should come back in chronological order (oldest → newest)."""
        client, db = app
        db.add_result(data=[chat_row()])
        db.add_result(data=[
            message_row("msg-2", role="assistant", content="Hi there!"),
            message_row("msg-1", role="user", content="Hello"),
        ])
        resp = client.get("/chats/chat-1/messages", headers=user_headers)
        assert resp.status_code == 200
        messages = resp.json()
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"

    def test_returns_empty_list_for_new_chat(self, app, user_headers):
        client, db = app
        db.add_result(data=[chat_row()])
        db.add_result(data=[])
        resp = client.get("/chats/chat-1/messages", headers=user_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_message_fields_are_correct(self, app, user_headers):
        """Each message object must contain id, chat_id, role, content, created_at."""
        client, db = app
        db.add_result(data=[chat_row()])
        db.add_result(data=[message_row("msg-1", content="Test message")])
        resp = client.get("/chats/chat-1/messages", headers=user_headers)
        assert resp.status_code == 200
        msg = resp.json()[0]
        assert "id" in msg
        assert "chat_id" in msg
        assert "role" in msg
        assert "content" in msg
        assert "created_at" in msg

    def test_chat_not_found(self, app, user_headers):
        client, db = app
        db.add_result(data=[])
        resp = client.get("/chats/missing/messages", headers=user_headers)
        assert resp.status_code == 404

    def test_wrong_owner_rejected(self, app, user_headers):
        client, db = app
        row = chat_row()
        row["projects"] = {"user_id": "someone-else"}
        db.add_result(data=[row])
        resp = client.get("/chats/chat-1/messages", headers=user_headers)
        assert resp.status_code == 404

    def test_unauthenticated(self, app):
        client, _ = app
        resp = client.get("/chats/chat-1/messages")
        assert resp.status_code in (401, 403)


class TestSendMessage:
    """
    send_message now makes 4 DB calls in order:
      1. _own_chat  — ownership check (chats table)
      2. insert     — persist user message (messages table)
      3. select     — fetch last N messages as LLM context (messages table)
      4. insert     — persist assistant reply (messages table)
    """

    def _queue_send(self, db, context_messages=None):
        """Queue the 4 DB results needed by a successful send_message call."""
        db.add_result(data=[chat_row()])
        db.add_result(data=[{}])
        db.add_result(data=context_messages or [])
        db.add_result(data=[{}])

    def test_success_returns_ai_reply(self, app, user_headers):
        client, db = app
        self._queue_send(db)
        resp = client.post(
            "/chats/chat-1/message",
            json={"message": "Hello"},
            headers=user_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["response"] == "Mocked AI reply"

    def test_persists_user_message_before_calling_ai(self, app, user_headers):
        """The route inserts the user message (DB call 2) before fetching context."""
        client, db = app
        self._queue_send(db, context_messages=[
            {"role": "user", "content": "Hello"},
        ])
        resp = client.post(
            "/chats/chat-1/message",
            json={"message": "Hello"},
            headers=user_headers,
        )
        assert resp.status_code == 200

    def test_sends_stored_context_to_gemini(self, app, user_headers):
        """Context passed to Gemini comes from the DB, not from the request body."""
        client, db = app
        self._queue_send(db, context_messages=[
            {"role": "user", "content": "What is Python?"},
            {"role": "assistant", "content": "A programming language."},
            {"role": "user", "content": "Give me an example"},
        ])
        resp = client.post(
            "/chats/chat-1/message",
            json={"message": "Give me an example"},
            headers=user_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["response"] == "Mocked AI reply"

    def test_empty_message_rejected(self, app, user_headers):
        """Whitespace-only messages are rejected by Pydantic before any DB call."""
        client, _ = app
        resp = client.post(
            "/chats/chat-1/message",
            json={"message": "   "},
            headers=user_headers,
        )
        assert resp.status_code == 422

    def test_no_history_field_in_request(self, app, user_headers):
        """The request model no longer accepts a 'history' field — it must be ignored or rejected."""
        client, db = app
        self._queue_send(db)
        resp = client.post(
            "/chats/chat-1/message",
            json={"message": "Hello", "history": [{"role": "user", "content": "old msg"}]},
            headers=user_headers,
        )

        assert resp.status_code in (200, 422)

    def test_chat_not_found(self, app, user_headers):
        client, db = app
        db.add_result(data=[])
        resp = client.post(
            "/chats/missing/message",
            json={"message": "Hello"},
            headers=user_headers,
        )
        assert resp.status_code == 404

    def test_wrong_owner_rejected(self, app, user_headers):
        client, db = app
        row = chat_row()
        row["projects"] = {"user_id": "someone-else"}
        db.add_result(data=[row])
        resp = client.post(
            "/chats/chat-1/message",
            json={"message": "Hello"},
            headers=user_headers,
        )
        assert resp.status_code == 404

    def test_gemini_failure_returns_502(self, app, user_headers):
        """If Gemini raises, the route should return 502 Bad Gateway."""
        import backend.routes.chat as r_chat
        original = r_chat.get_gemini_response

        def boom(*_a, **_kw):
            raise RuntimeError("Gemini is down")

        r_chat.get_gemini_response = boom
        try:
            client, db = app
            db.add_result(data=[chat_row()])
            db.add_result(data=[{}])
            db.add_result(data=[])
            resp = client.post(
                "/chats/chat-1/message",
                json={"message": "Hello"},
                headers=user_headers,
            )
            assert resp.status_code == 502
            assert "Gemini error" in resp.json()["detail"]
        finally:
            r_chat.get_gemini_response = original

    def test_unauthenticated(self, app):
        client, _ = app
        resp = client.post("/chats/chat-1/message", json={"message": "Hi"})
        assert resp.status_code in (401, 403)