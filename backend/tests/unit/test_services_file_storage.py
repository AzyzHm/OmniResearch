from unittest.mock import MagicMock

import services.file_storage as file_storage


class TestUploadCollectionFile:
    def test_uploads_with_content_type_and_upsert(self, monkeypatch):
        fake_db = MagicMock()
        monkeypatch.setattr(file_storage, "get_supabase", lambda: fake_db)

        file_storage.upload_collection_file("col-1/item-1/report.pdf", b"raw", "application/pdf")

        bucket = fake_db.storage.from_.return_value
        fake_db.storage.from_.assert_called_once_with("collection-files")
        bucket.upload.assert_called_once_with(
            "col-1/item-1/report.pdf",
            b"raw",
            {"content-type": "application/pdf", "upsert": "true"},
        )


class TestDownloadCollectionFile:
    def test_downloads_from_configured_bucket(self, monkeypatch):
        fake_db = MagicMock()
        fake_db.storage.from_.return_value.download.return_value = b"file bytes"
        monkeypatch.setattr(file_storage, "get_supabase", lambda: fake_db)

        result = file_storage.download_collection_file("col-1/item-1/report.pdf")

        assert result == b"file bytes"
        fake_db.storage.from_.assert_called_once_with("collection-files")

    def test_propagates_errors(self, monkeypatch):
        fake_db = MagicMock()
        fake_db.storage.from_.return_value.download.side_effect = RuntimeError("not found")
        monkeypatch.setattr(file_storage, "get_supabase", lambda: fake_db)

        try:
            file_storage.download_collection_file("missing/path")
            assert False, "expected RuntimeError to propagate"
        except RuntimeError:
            pass


class TestDeleteCollectionFile:
    def test_removes_the_object(self, monkeypatch):
        fake_db = MagicMock()
        monkeypatch.setattr(file_storage, "get_supabase", lambda: fake_db)

        file_storage.delete_collection_file("col-1/item-1/report.pdf")

        fake_db.storage.from_.return_value.remove.assert_called_once_with(["col-1/item-1/report.pdf"])

    def test_swallows_errors_so_item_deletion_never_blocks(self, monkeypatch, capsys):
        fake_db = MagicMock()
        fake_db.storage.from_.return_value.remove.side_effect = RuntimeError("bucket unreachable")
        monkeypatch.setattr(file_storage, "get_supabase", lambda: fake_db)

        file_storage.delete_collection_file("col-1/item-1/report.pdf")  # must not raise

        assert "Warning" in capsys.readouterr().out
