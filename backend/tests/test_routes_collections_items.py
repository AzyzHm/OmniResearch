from unittest.mock import MagicMock

from tests.conftest import collection_row

ITEM_PDF = {
    "id": "item-1", "collection_id": "col-1", "name": "report.pdf",
    "source_type": "pdf", "is_active": True, "status": "ready",
    "chunk_count": 4, "page_count": 12, "word_count": None,
    "storage_path": "col-1/item-1/report.pdf", "error_message": None,
    "created_at": "2026-01-01T00:00:00Z",
}

ITEM_URL = {
    "id": "item-2", "collection_id": "col-1", "name": "https://example.com",
    "source_type": "url", "is_active": True, "status": "ready",
    "chunk_count": 2, "page_count": None, "word_count": None,
    "storage_path": None, "error_message": None,
    "created_at": "2026-01-01T00:00:00Z",
}

ITEM_PDF_NO_STORAGE = {**ITEM_PDF, "id": "item-4", "storage_path": None}


class TestGetItemContent:
    def test_pdf_returns_file_bytes(self, app, user_headers, monkeypatch):
        import routes.collections.items as items_mod

        monkeypatch.setattr(items_mod, "download_collection_file", lambda path: b"%PDF-1.4 fake")

        client, db = app
        db.add_result(data=[collection_row()])  # _own_collection
        db.add_result(data=[ITEM_PDF])  # item lookup

        resp = client.get("/collections/col-1/items/item-1/content", headers=user_headers)

        assert resp.status_code == 200
        assert resp.content == b"%PDF-1.4 fake"
        assert resp.headers["content-type"] == "application/pdf"
        assert 'filename="report.pdf"' in resp.headers["content-disposition"]

    def test_txt_returns_plain_text(self, app, user_headers, monkeypatch):
        import routes.collections.items as items_mod

        monkeypatch.setattr(items_mod, "download_collection_file", lambda path: b"hello world")

        client, db = app
        db.add_result(data=[collection_row()])
        item = {**ITEM_PDF, "id": "item-3", "name": "notes.txt", "source_type": "txt",
                "storage_path": "col-1/item-3/notes.txt"}
        db.add_result(data=[item])

        resp = client.get("/collections/col-1/items/item-3/content", headers=user_headers)

        assert resp.status_code == 200
        assert resp.content == b"hello world"
        assert resp.headers["content-type"] == "text/plain; charset=utf-8"

    def test_item_not_found_returns_404(self, app, user_headers):
        client, db = app
        db.add_result(data=[collection_row()])
        db.add_result(data=[])  # item lookup: no rows

        resp = client.get("/collections/col-1/items/missing/content", headers=user_headers)

        assert resp.status_code == 404

    def test_url_item_has_no_content_returns_400(self, app, user_headers):
        client, db = app
        db.add_result(data=[collection_row()])
        db.add_result(data=[ITEM_URL])

        resp = client.get("/collections/col-1/items/item-2/content", headers=user_headers)

        assert resp.status_code == 400

    def test_missing_storage_path_returns_404(self, app, user_headers):
        """Pre-migration items, or items whose upload to storage failed,
        have no storage_path — the endpoint should say so, not 500."""
        client, db = app
        db.add_result(data=[collection_row()])
        db.add_result(data=[ITEM_PDF_NO_STORAGE])

        resp = client.get("/collections/col-1/items/item-4/content", headers=user_headers)

        assert resp.status_code == 404

    def test_download_failure_returns_502(self, app, user_headers, monkeypatch):
        import routes.collections.items as items_mod

        def _raise(path):
            raise RuntimeError("storage unreachable")

        monkeypatch.setattr(items_mod, "download_collection_file", _raise)

        client, db = app
        db.add_result(data=[collection_row()])
        db.add_result(data=[ITEM_PDF])

        resp = client.get("/collections/col-1/items/item-1/content", headers=user_headers)

        assert resp.status_code == 502

    def test_wrong_owner_returns_404(self, app, user_headers):
        client, db = app
        other_owner_collection = {**collection_row(), "projects": {"user_id": "someone-else"}}
        db.add_result(data=[other_owner_collection])  # _own_collection

        resp = client.get("/collections/col-1/items/item-1/content", headers=user_headers)

        assert resp.status_code == 404


class TestDeleteItem:
    def test_deletes_stored_file_when_storage_path_present(self, app, user_headers, monkeypatch):
        import routes.collections.items as items_mod

        delete_calls = []
        monkeypatch.setattr(
            items_mod, "delete_collection_file", lambda path: delete_calls.append(path)
        )

        client, db = app
        db.add_result(data=[collection_row()])  # _own_collection
        db.add_result(data=[{"storage_path": "col-1/item-1/report.pdf"}])  # storage_path lookup
        db.add_result(data=[ITEM_PDF])  # the delete() call itself

        resp = client.delete("/collections/col-1/items/item-1", headers=user_headers)

        assert resp.status_code == 204
        assert delete_calls == ["col-1/item-1/report.pdf"]

    def test_skips_storage_delete_when_no_storage_path(self, app, user_headers, monkeypatch):
        import routes.collections.items as items_mod

        delete_mock = MagicMock()
        monkeypatch.setattr(items_mod, "delete_collection_file", delete_mock)

        client, db = app
        db.add_result(data=[collection_row()])
        db.add_result(data=[{"storage_path": None}])
        db.add_result(data=[ITEM_URL])

        resp = client.delete("/collections/col-1/items/item-2", headers=user_headers)

        assert resp.status_code == 204
        delete_mock.assert_not_called()

    def test_skips_storage_delete_when_item_already_gone(self, app, user_headers, monkeypatch):
        """If the select-before-delete finds nothing, there's nothing to
        clean up in storage either — must not raise on an empty lookup."""
        import routes.collections.items as items_mod

        delete_mock = MagicMock()
        monkeypatch.setattr(items_mod, "delete_collection_file", delete_mock)

        client, db = app
        db.add_result(data=[collection_row()])
        db.add_result(data=[])  # storage_path lookup: item already gone
        db.add_result(data=[])  # the delete() call itself

        resp = client.delete("/collections/col-1/items/item-1", headers=user_headers)

        assert resp.status_code == 204
        delete_mock.assert_not_called()