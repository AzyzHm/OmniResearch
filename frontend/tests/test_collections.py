import frontend.services.collections as collections


class _FakeUploadedFile:
    """Stand-in for a Streamlit UploadedFile."""
    def __init__(self, name: str, content: bytes, file_type: str | None = "text/plain"):
        self.name = name
        self.type = file_type
        self._content = content

    def getvalue(self):
        return self._content


class TestListCollections:
    def test_calls_correct_endpoint(self, mock_call):
        stub = mock_call(collections, return_value=[{"id": "col-1"}])
        result = collections.list_collections("tok", "proj-1")
        stub.assert_called_once_with("GET", "/projects/proj-1/collections", token="tok")
        assert result == [{"id": "col-1"}]

    def test_none_response_falls_back_to_empty_list(self, mock_call):
        mock_call(collections, return_value=None)
        assert collections.list_collections("tok", "proj-1") == []


class TestCreateCollection:
    def test_calls_correct_endpoint(self, mock_call):
        stub = mock_call(collections, return_value={"id": "col-1", "name": "Docs"})
        collections.create_collection("tok", "proj-1", "Docs", "documents")
        stub.assert_called_once_with(
            "POST", "/projects/proj-1/collections",
            token="tok", json={"name": "Docs", "type": "documents"},
        )


class TestDeleteCollection:
    def test_calls_correct_endpoint(self, mock_call):
        stub = mock_call(collections, return_value=None)
        collections.delete_collection("tok", "col-1")
        stub.assert_called_once_with("DELETE", "/collections/col-1", token="tok")


class TestListCollectionItems:
    def test_calls_correct_endpoint(self, mock_call):
        stub = mock_call(collections, return_value=[{"id": "item-1"}])
        result = collections.list_collection_items("tok", "col-1")
        stub.assert_called_once_with("GET", "/collections/col-1/items", token="tok")
        assert result == [{"id": "item-1"}]

    def test_none_response_falls_back_to_empty_list(self, mock_call):
        mock_call(collections, return_value=None)
        assert collections.list_collection_items("tok", "col-1") == []


class TestUploadCollectionItems:
    def test_builds_files_tuple_correctly(self, mock_call_multipart):
        stub = mock_call_multipart(collections, return_value=[{"id": "item-1"}])
        uploaded = [_FakeUploadedFile("report.pdf", b"%PDF-1.4...", "application/pdf")]
        result = collections.upload_collection_items("tok", "col-1", uploaded)

        stub.assert_called_once_with(
            "POST", "/collections/col-1/items",
            token="tok",
            files=[("files", ("report.pdf", b"%PDF-1.4...", "application/pdf"))],
        )
        assert result == [{"id": "item-1"}]

    def test_multiple_files(self, mock_call_multipart):
        stub = mock_call_multipart(collections, return_value=[])
        uploaded = [
            _FakeUploadedFile("a.txt", b"hello", "text/plain"),
            _FakeUploadedFile("b.pdf", b"world", "application/pdf"),
        ]
        collections.upload_collection_items("tok", "col-1", uploaded)
        _, kwargs = stub.call_args
        assert len(kwargs["files"]) == 2

    def test_missing_mime_type_defaults(self, mock_call_multipart):
        stub = mock_call_multipart(collections, return_value=[])
        uploaded = [_FakeUploadedFile("a.txt", b"hello", file_type=None)]
        collections.upload_collection_items("tok", "col-1", uploaded)
        _, kwargs = stub.call_args
        assert kwargs["files"][0][1][2] == "application/octet-stream"

    def test_none_response_falls_back_to_empty_list(self, mock_call_multipart):
        mock_call_multipart(collections, return_value=None)
        uploaded = [_FakeUploadedFile("a.txt", b"hello")]
        assert collections.upload_collection_items("tok", "col-1", uploaded) == []


class TestToggleCollectionItem:
    def test_calls_correct_endpoint(self, mock_call):
        stub = mock_call(collections, return_value={"id": "item-1", "is_active": False})
        collections.toggle_collection_item("tok", "col-1", "item-1", False)
        stub.assert_called_once_with(
            "PATCH", "/collections/col-1/items/item-1",
            token="tok", json={"is_active": False},
        )


class TestBulkUpdateCollectionItems:
    def test_calls_correct_endpoint(self, mock_call):
        stub = mock_call(collections, return_value=[{"id": "item-1"}])
        updates = [{"item_id": "item-1", "is_active": True}]
        result = collections.bulk_update_collection_items("tok", "col-1", updates)
        stub.assert_called_once_with(
            "PATCH", "/collections/col-1/items/bulk",
            token="tok", json={"updates": updates},
        )
        assert result == [{"id": "item-1"}]

    def test_none_response_falls_back_to_empty_list(self, mock_call):
        mock_call(collections, return_value=None)
        assert collections.bulk_update_collection_items("tok", "col-1", []) == []


class TestDeleteCollectionItem:
    def test_calls_correct_endpoint(self, mock_call):
        stub = mock_call(collections, return_value=None)
        collections.delete_collection_item("tok", "col-1", "item-1")
        stub.assert_called_once_with(
            "DELETE", "/collections/col-1/items/item-1", token="tok"
        )


class TestAddUrlItem:
    def test_calls_correct_endpoint(self, mock_call):
        stub = mock_call(collections, return_value={"id": "item-1", "url": "https://example.com"})
        collections.add_url_item("tok", "col-1", "https://example.com")
        stub.assert_called_once_with(
            "POST", "/collections/col-1/items/url",
            token="tok", json={"url": "https://example.com"},
        )