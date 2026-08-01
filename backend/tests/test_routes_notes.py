from backend.tests.conftest import project_row, note_row, note_item_row, message_row


def message_with_chat(msg_id="msg-1", chat_id="chat-1", project_id="proj-1",
                       role="assistant", content="Hi there!", sources=None):
    row = message_row(msg_id, chat_id, role, content)
    row["sources"] = sources #type: ignore
    row["chats"] = {"project_id": project_id} #type: ignore
    return row


class TestListNotes:
    def test_returns_all_notes(self, app, user_headers):
        client, db = app
        db.add_result(data=[project_row()])
        db.add_result(data=[note_row(), note_row("note-2", name="B")])
        resp = client.get("/projects/proj-1/notes", headers=user_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_returns_empty_list_when_no_notes(self, app, user_headers):
        client, db = app
        db.add_result(data=[project_row()])
        db.add_result(data=[])
        resp = client.get("/projects/proj-1/notes", headers=user_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_project_not_found(self, app, user_headers):
        client, db = app
        db.add_result(data=[])
        resp = client.get("/projects/bad/notes", headers=user_headers)
        assert resp.status_code == 404

    def test_unauthenticated(self, app):
        client, _ = app
        resp = client.get("/projects/proj-1/notes")
        assert resp.status_code in (401, 403)


class TestCreateNote:
    def test_success(self, app, user_headers):
        client, db = app
        db.add_result(data=[project_row()])
        db.add_result(data=[])  # existing-names lookup
        db.add_result(data=[note_row()])
        resp = client.post("/projects/proj-1/notes", json={"name": "My Note"}, headers=user_headers)
        assert resp.status_code == 201
        assert resp.json()["name"] == "My Note"

    def test_duplicate_name_gets_numbered(self, app, user_headers):
        client, db = app
        db.add_result(data=[project_row()])
        db.add_result(data=[{"id": "note-1", "name": "Key Findings"}])  # existing-names lookup
        db.add_result(data=[note_row(name="Key Findings (2)")])
        resp = client.post(
            "/projects/proj-1/notes", json={"name": "Key Findings"}, headers=user_headers
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "Key Findings (2)"

    def test_empty_name_rejected(self, app, user_headers):
        client, _ = app
        resp = client.post("/projects/proj-1/notes", json={"name": "   "}, headers=user_headers)
        assert resp.status_code == 422

    def test_project_not_found(self, app, user_headers):
        client, db = app
        db.add_result(data=[])
        resp = client.post("/projects/bad/notes", json={"name": "X"}, headers=user_headers)
        assert resp.status_code == 404


class TestRenameNote:
    def test_success(self, app, user_headers):
        client, db = app
        db.add_result(data=[note_row()])
        db.add_result(data=[])  # existing-names lookup (excluding self)
        db.add_result(data=[note_row(name="Renamed")])
        resp = client.put("/notes/note-1", json={"name": "Renamed"}, headers=user_headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Renamed"

    def test_duplicate_name_gets_numbered(self, app, user_headers):
        client, db = app
        db.add_result(data=[note_row()])
        db.add_result(data=[{"id": "note-2", "name": "Other Note"}])  # existing-names lookup
        db.add_result(data=[note_row(name="Other Note (2)")])
        resp = client.put("/notes/note-1", json={"name": "Other Note"}, headers=user_headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Other Note (2)"

    def test_empty_name_rejected(self, app, user_headers):
        client, _ = app
        resp = client.put("/notes/note-1", json={"name": "  "}, headers=user_headers)
        assert resp.status_code == 422

    def test_note_not_found(self, app, user_headers):
        client, db = app
        db.add_result(data=[])
        resp = client.put("/notes/missing", json={"name": "X"}, headers=user_headers)
        assert resp.status_code == 404

    def test_wrong_owner_rejected(self, app, user_headers):
        client, db = app
        row = note_row()
        row["projects"] = {"user_id": "someone-else"}
        db.add_result(data=[row])
        resp = client.put("/notes/note-1", json={"name": "X"}, headers=user_headers)
        assert resp.status_code == 404


class TestDeleteNote:
    def test_success(self, app, user_headers):
        client, db = app
        db.add_result(data=[note_row()])
        db.add_result(data=[])
        resp = client.delete("/notes/note-1", headers=user_headers)
        assert resp.status_code == 204

    def test_note_not_found(self, app, user_headers):
        client, db = app
        db.add_result(data=[])
        resp = client.delete("/notes/missing", headers=user_headers)
        assert resp.status_code == 404

    def test_unauthenticated(self, app):
        client, _ = app
        resp = client.delete("/notes/note-1")
        assert resp.status_code in (401, 403)


class TestListNoteItems:
    """GET /notes/{note_id}/items — saved messages, flattened with their sources."""

    def test_returns_items_with_message_fields(self, app, user_headers):
        client, db = app
        db.add_result(data=[note_row()])  # ownership
        db.add_result(data=[
            note_item_row(sources=[{"index": 1, "source_name": "report.pdf"}])
        ])
        resp = client.get("/notes/note-1/items", headers=user_headers)
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) == 1
        assert items[0]["chat_id"] == "chat-1"
        assert items[0]["role"] == "assistant"
        assert items[0]["content"] == "Hi there!"
        assert items[0]["sources"][0]["source_name"] == "report.pdf"

    def test_returns_empty_list_for_new_note(self, app, user_headers):
        client, db = app
        db.add_result(data=[note_row()])
        db.add_result(data=[])
        resp = client.get("/notes/note-1/items", headers=user_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_note_not_found(self, app, user_headers):
        client, db = app
        db.add_result(data=[])
        resp = client.get("/notes/missing/items", headers=user_headers)
        assert resp.status_code == 404


class TestCreateNoteItem:
    """POST /notes/{note_id}/items — save a chat message into a note."""

    def test_success(self, app, user_headers):
        client, db = app
        db.add_result(data=[note_row()])                    # own note
        db.add_result(data=[message_with_chat()])            # own message (joined w/ chat->project)
        db.add_result(data=[])                                # duplicate-save check (none)
        db.add_result(data=[{"id": "item-1", "note_id": "note-1",
                              "message_id": "msg-1", "created_at": note_row()["created_at"]}])
        resp = client.post(
            "/notes/note-1/items", json={"message_id": "msg-1"}, headers=user_headers
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["message_id"] == "msg-1"
        assert body["chat_id"] == "chat-1"
        assert body["content"] == "Hi there!"

    def test_duplicate_save_rejected(self, app, user_headers):
        client, db = app
        db.add_result(data=[note_row()])
        db.add_result(data=[message_with_chat()])
        db.add_result(data=[{"id": "item-existing"}])  # already saved
        resp = client.post(
            "/notes/note-1/items", json={"message_id": "msg-1"}, headers=user_headers
        )
        assert resp.status_code == 409

    def test_message_not_found(self, app, user_headers):
        client, db = app
        db.add_result(data=[note_row()])
        db.add_result(data=[])  # message lookup empty
        resp = client.post(
            "/notes/note-1/items", json={"message_id": "missing"}, headers=user_headers
        )
        assert resp.status_code == 404

    def test_message_from_other_project_rejected(self, app, user_headers):
        """A message belonging to a chat in a different project can't be saved here."""
        client, db = app
        db.add_result(data=[note_row(project_id="proj-1")])
        db.add_result(data=[message_with_chat(project_id="proj-OTHER")])
        resp = client.post(
            "/notes/note-1/items", json={"message_id": "msg-1"}, headers=user_headers
        )
        assert resp.status_code == 404

    def test_note_not_found(self, app, user_headers):
        client, db = app
        db.add_result(data=[])
        resp = client.post(
            "/notes/missing/items", json={"message_id": "msg-1"}, headers=user_headers
        )
        assert resp.status_code == 404


class TestDeleteNoteItem:
    """DELETE /notes/{note_id}/items/{item_id} — unsave without deleting the note."""

    def test_success(self, app, user_headers):
        client, db = app
        db.add_result(data=[note_row()])
        db.add_result(data=[])
        resp = client.delete("/notes/note-1/items/item-1", headers=user_headers)
        assert resp.status_code == 204

    def test_note_not_found(self, app, user_headers):
        client, db = app
        db.add_result(data=[])
        resp = client.delete("/notes/missing/items/item-1", headers=user_headers)
        assert resp.status_code == 404

    def test_unauthenticated(self, app):
        client, _ = app
        resp = client.delete("/notes/note-1/items/item-1")
        assert resp.status_code in (401, 403)