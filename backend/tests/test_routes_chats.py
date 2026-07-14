from backend.tests.conftest import project_row, chat_row, message_row


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
    """GET /chats/{chat_id}/messages — the persistent history endpoint."""

    def test_returns_messages_oldest_first(self, app, user_headers):
        client, db = app
        db.add_result(data=[chat_row()])  # ownership check
        db.add_result(data=[
            message_row("msg-2", role="assistant", content="Hi there!"),
            message_row("msg-1", role="user", content="Hello"),
        ])
        resp = client.get("/chats/chat-1/messages", headers=user_headers)
        assert resp.status_code == 200
        messages = resp.json()
        assert len(messages) == 2
        assert messages[0]["role"] == "user"        # msg-1 was older -> first after reversal
        assert messages[1]["role"] == "assistant"    # msg-2 was newer -> last

    def test_returns_empty_list_for_new_chat(self, app, user_headers):
        client, db = app
        db.add_result(data=[chat_row()])
        db.add_result(data=[])
        resp = client.get("/chats/chat-1/messages", headers=user_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_message_fields_are_correct(self, app, user_headers):
        client, db = app
        db.add_result(data=[chat_row()])
        db.add_result(data=[message_row("msg-1", content="Test message")])
        resp = client.get("/chats/chat-1/messages", headers=user_headers)
        assert resp.status_code == 200
        msg = resp.json()[0]
        for field in ("id", "chat_id", "role", "content", "created_at"):
            assert field in msg

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


def _queue_send(db, history=None, daily_token_limit=None, tokens_used_today=None):
    db.add_result(data=[chat_row()])                                   # 1. ownership
    db.add_result(data=[{"daily_token_limit": daily_token_limit}]       # 2. quota limit
                   if daily_token_limit is not None else [])
    db.add_result(data=tokens_used_today or [])                         # 3. quota used
    db.add_result(data=history or [])                                  # 4. history fetch
    db.add_result(data=[{}])                                            # 5. insert user msg
    db.add_result(data=[{}])                                            # 7. insert assistant reply


class TestSendMessage:
    """
    send_message's actual DB call order is:
      1. _own_chat            — ownership check (chats table)
      2. get_daily_token_limit — quota check (users table)
      3. get_tokens_used_today — quota check (llm_usage table)
      4. select messages      — fetch history *before* the new message exists
      5. insert               — persist the user message
      6. [RAG graph runs — mocked via db.rag_graph, no DB call]
      7. insert               — persist the assistant reply
    """

    def _queue_send(self, db, history=None, daily_token_limit=None, tokens_used_today=None):
        _queue_send(db, history=history, daily_token_limit=daily_token_limit,
                    tokens_used_today=tokens_used_today)

    def test_success_returns_ai_reply(self, app, user_headers):
        client, db = app
        self._queue_send(db)
        resp = client.post("/chats/chat-1/message", json={"message": "Hello"}, headers=user_headers)
        assert resp.status_code == 200
        assert resp.json()["response"] == "Mocked AI reply"

    def test_custom_graph_answer_is_returned(self, app, user_headers):
        """The route should return whatever the RAG graph produces, not a hardcoded string."""
        client, db = app
        db.rag_graph.answer = "The sky is blue because of Rayleigh scattering."
        self._queue_send(db)
        resp = client.post("/chats/chat-1/message", json={"message": "Why is the sky blue?"}, headers=user_headers)
        assert resp.status_code == 200
        assert resp.json()["response"] == "The sky is blue because of Rayleigh scattering."

    def test_graph_receives_correct_state(self, app, user_headers):
        """project_id, chat_id, user_id, and query must be threaded into the graph state."""
        client, db = app
        self._queue_send(db, history=[{"role": "user", "content": "earlier msg"}])
        resp = client.post("/chats/chat-1/message", json={"message": "Follow up"}, headers=user_headers)
        assert resp.status_code == 200
        state = db.rag_graph.last_invoke_state
        assert state["project_id"] == "proj-1"
        assert state["chat_id"] == "chat-1"
        assert state["user_id"] == "user-123"
        assert state["query"] == "Follow up"
        assert state["history"] == [{"role": "user", "content": "earlier msg"}]

    def test_empty_message_rejected(self, app, user_headers):
        client, _ = app
        resp = client.post("/chats/chat-1/message", json={"message": "   "}, headers=user_headers)
        assert resp.status_code == 422

    def test_no_history_field_in_request(self, app, user_headers):
        """The request model has no 'history' field — history is DB-driven now."""
        client, db = app
        self._queue_send(db)
        resp = client.post(
            "/chats/chat-1/message",
            json={"message": "Hello", "history": [{"role": "user", "content": "ignored"}]},
            headers=user_headers,
        )
        assert resp.status_code in (200, 422)

    def test_chat_not_found(self, app, user_headers):
        client, db = app
        db.add_result(data=[])
        resp = client.post("/chats/missing/message", json={"message": "Hello"}, headers=user_headers)
        assert resp.status_code == 404

    def test_wrong_owner_rejected(self, app, user_headers):
        client, db = app
        row = chat_row()
        row["projects"] = {"user_id": "someone-else"}
        db.add_result(data=[row])
        resp = client.post("/chats/chat-1/message", json={"message": "Hello"}, headers=user_headers)
        assert resp.status_code == 404

    def test_rag_graph_failure_returns_502(self, app, user_headers):
        """If the RAG graph raises, the route should return 502 with the raw error in the detail."""
        client, db = app
        self._queue_send(db)
        db.rag_graph.raise_exc = RuntimeError("graph exploded")
        resp = client.post("/chats/chat-1/message", json={"message": "Hello"}, headers=user_headers)
        assert resp.status_code == 502
        assert resp.json()["detail"] == "graph exploded"

    def test_unauthenticated(self, app):
        client, _ = app
        resp = client.post("/chats/chat-1/message", json={"message": "Hi"})
        assert resp.status_code in (401, 403)


class TestQuotaEnforcement:
    """
    enforce_daily_quota() runs right after ownership is verified and before
    any history fetch/graph invocation — an exhausted user should be blocked
    immediately, with no message persisted and no graph call made.
    """

    def test_message_returns_429_when_quota_exceeded(self, app, user_headers):
        client, db = app
        db.add_result(data=[chat_row()])                         # ownership
        db.add_result(data=[{"daily_token_limit": 100}])          # quota limit = 100
        db.add_result(data=[{"total_tokens": 150}])               # 150 used >= 100
        resp = client.post("/chats/chat-1/message", json={"message": "Hello"}, headers=user_headers)
        assert resp.status_code == 429
        detail = resp.json()["detail"]
        assert detail["code"] == "quota_exceeded"
        assert detail["used"] == 150
        assert detail["limit"] == 100

    def test_message_allowed_when_under_quota(self, app, user_headers):
        client, db = app
        _queue_send(db, daily_token_limit=100, tokens_used_today=[{"total_tokens": 50}])
        resp = client.post("/chats/chat-1/message", json={"message": "Hello"}, headers=user_headers)
        assert resp.status_code == 200

    def test_message_stream_emits_error_event_when_quota_exceeded(self, app, user_headers):
        client, db = app
        db.add_result(data=[chat_row()])                         # ownership
        db.add_result(data=[{"daily_token_limit": 100}])          # quota limit = 100
        db.add_result(data=[{"total_tokens": 100}])               # exactly at the limit
        resp = client.post("/chats/chat-1/message/stream", json={"message": "Hello"}, headers=user_headers)
        assert resp.status_code == 200  # SSE always 200; error is in the event body
        assert '"type": "error"' in resp.text
        assert '"code": "quota_exceeded"' in resp.text

    def test_default_quota_used_when_no_limit_row(self, app, user_headers):
        """A user row with no daily_token_limit column falls back to the default (80,000)."""
        client, db = app
        _queue_send(db, daily_token_limit=None, tokens_used_today=[{"total_tokens": 79_999}])
        resp = client.post("/chats/chat-1/message", json={"message": "Hello"}, headers=user_headers)
        assert resp.status_code == 200


class TestSendMessageStream:
    """POST /chats/{chat_id}/message/stream — Server-Sent Events variant."""

    def _queue_stream(self, db, history=None):
        db.add_result(data=[chat_row()])           # ownership
        db.add_result(data=[])                      # quota limit (default)
        db.add_result(data=[])                      # quota used (0 tokens)
        db.add_result(data=history or [])           # history fetch
        db.add_result(data=[{}])                     # insert user msg
        db.add_result(data=[{}])                     # insert assistant reply (after stream completes)

    def test_stream_returns_200_and_sse_content_type(self, app, user_headers):
        client, db = app
        self._queue_stream(db)
        resp = client.post("/chats/chat-1/message/stream", json={"message": "Hello"}, headers=user_headers)
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]

    def test_stream_emits_node_and_done_events(self, app, user_headers):
        client, db = app
        self._queue_stream(db)
        resp = client.post("/chats/chat-1/message/stream", json={"message": "Hello"}, headers=user_headers)
        body = resp.text
        assert '"type": "node"' in body
        assert '"type": "done"' in body
        assert "Mocked AI reply" in body

    def test_stream_emits_error_event_on_graph_failure(self, app, user_headers):
        client, db = app
        self._queue_stream(db)
        db.rag_graph.raise_exc = RuntimeError("stream exploded")
        resp = client.post("/chats/chat-1/message/stream", json={"message": "Hello"}, headers=user_headers)
        assert resp.status_code == 200  # SSE always returns 200; error is in the event body
        assert '"type": "error"' in resp.text
        assert "stream exploded" in resp.text

    def test_stream_chat_not_found(self, app, user_headers):
        client, db = app
        db.add_result(data=[])
        resp = client.post("/chats/missing/message/stream", json={"message": "Hello"}, headers=user_headers)
        assert resp.status_code == 404

    def test_stream_unauthenticated(self, app):
        client, _ = app
        resp = client.post("/chats/chat-1/message/stream", json={"message": "Hi"})
        assert resp.status_code in (401, 403)