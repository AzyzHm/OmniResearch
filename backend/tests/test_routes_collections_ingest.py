from backend.tests.conftest import collection_row


def _patch_pipeline(monkeypatch):
    import backend.routes.collections.ingest as ingest_mod

    monkeypatch.setattr(ingest_mod, "extract_pdf", lambda raw: "pdf text")
    monkeypatch.setattr(ingest_mod, "extract_txt", lambda raw: "txt text")
    monkeypatch.setattr(ingest_mod, "embed_texts", lambda chunks: [[0.1, 0.2] for _ in chunks])
    monkeypatch.setattr(ingest_mod, "fetch_url_markdown", lambda url: "fetched markdown")
    monkeypatch.setattr(ingest_mod, "add_item_chunks", lambda **kwargs: None)


class TestUploadItems:
    def test_mixed_pdf_and_txt_batch_succeeds(self, app, user_headers, monkeypatch):
        _patch_pipeline(monkeypatch)
        client, db = app
        db.add_result(data=[collection_row()])  # _own_collection lookup
        db.add_result(data=[{"id": "item-1", "collection_id": "col-1", "name": "a.pdf",
                              "source_type": "pdf", "is_active": True, "status": "processing",
                              "chunk_count": 0, "created_at": "2026-01-01T00:00:00Z"}])
        db.add_result(data=[{"id": "item-2", "collection_id": "col-1", "name": "b.txt",
                              "source_type": "txt", "is_active": True, "status": "processing",
                              "chunk_count": 0, "created_at": "2026-01-01T00:00:00Z"}])

        resp = client.post(
            "/collections/col-1/items",
            files=[
                ("files", ("a.pdf", b"%PDF-1.4 fake", "application/pdf")),
                ("files", ("b.txt", b"plain text", "text/plain")),
            ],
            headers=user_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 2
        assert {item["source_type"] for item in body} == {"pdf", "txt"}

    def test_rejects_unsupported_extension(self, app, user_headers, monkeypatch):
        _patch_pipeline(monkeypatch)
        client, db = app
        db.add_result(data=[collection_row()])

        resp = client.post(
            "/collections/col-1/items",
            files=[("files", ("notes.docx", b"binary", "application/octet-stream"))],
            headers=user_headers,
        )
        assert resp.status_code == 400
        assert "notes.docx" in resp.json()["detail"]

    def test_rejects_unsupported_extension_within_mixed_batch(self, app, user_headers, monkeypatch):
        """One bad file in an otherwise-valid batch still rejects the whole request."""
        _patch_pipeline(monkeypatch)
        client, db = app
        db.add_result(data=[collection_row()])

        resp = client.post(
            "/collections/col-1/items",
            files=[
                ("files", ("a.pdf", b"%PDF-1.4 fake", "application/pdf")),
                ("files", ("virus.exe", b"binary", "application/octet-stream")),
            ],
            headers=user_headers,
        )
        assert resp.status_code == 400
        assert "virus.exe" in resp.json()["detail"]


class TestAddUrlItem:
    def test_add_url_succeeds_on_any_collection(self, app, user_headers, monkeypatch):
        """No more urls-only gate — a plain collection accepts a URL item too."""
        _patch_pipeline(monkeypatch)
        client, db = app
        db.add_result(data=[collection_row()])  # _own_collection
        db.add_result(data=[])  # _existing_urls
        db.add_result(data=[{"id": "item-3", "collection_id": "col-1",
                              "name": "https://example.com/article", "source_type": "url",
                              "is_active": True, "status": "processing", "chunk_count": 0,
                              "created_at": "2026-01-01T00:00:00Z"}])

        resp = client.post(
            "/collections/col-1/items/url",
            json={"url": "https://example.com/article"},
            headers=user_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["source_type"] == "url"

    def test_add_duplicate_url_rejected(self, app, user_headers, monkeypatch):
        _patch_pipeline(monkeypatch)
        client, db = app
        db.add_result(data=[collection_row()])
        db.add_result(data=[{"name": "https://example.com/article"}])  # _existing_urls

        resp = client.post(
            "/collections/col-1/items/url",
            json={"url": "https://example.com/article"},
            headers=user_headers,
        )
        assert resp.status_code == 400


class TestAddSearchResultItems:
    def test_add_search_results_succeeds_on_any_collection(self, app, user_headers, monkeypatch):
        _patch_pipeline(monkeypatch)
        client, db = app
        db.add_result(data=[collection_row()])  # _own_collection
        db.add_result(data=[])  # _existing_urls
        db.add_result(data=[{"id": "item-4", "collection_id": "col-1",
                              "name": "https://example.com/1", "source_type": "url",
                              "is_active": True, "status": "processing", "chunk_count": 0,
                              "created_at": "2026-01-01T00:00:00Z"}])

        resp = client.post(
            "/collections/col-1/items/from-search",
            json={"items": [{"url": "https://example.com/1", "title": "T", "content": "some content"}]},
            headers=user_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["added"]) == 1
        assert body["skipped"] == []