import logging
from unittest.mock import MagicMock

import pytest
from chromadb.errors import NotFoundError

from database import chroma_client


@pytest.fixture(autouse=True)
def _clear_chroma_cache():
    """get_chroma() is lru_cache'd; make sure the mock client from one test
    can't leak into the next."""
    chroma_client.get_chroma.cache_clear()
    yield
    chroma_client.get_chroma.cache_clear()


class TestDeleteChromaCollection:
    def test_not_found_error_is_silently_ignored(self, monkeypatch):
        """Deleting an already-gone collection is expected and must not raise
        or log anything — this is the documented 'safe to call even if it
        doesn't exist' behavior."""
        fake_client = MagicMock()
        fake_client.delete_collection.side_effect = NotFoundError("Collection [x] does not exist")
        monkeypatch.setattr(chroma_client, "get_chroma", lambda: fake_client)

        chroma_client.delete_chroma_collection("some-collection-id")

        fake_client.delete_collection.assert_called_once_with(name="some-collection-id")

    def test_other_exceptions_are_logged_not_swallowed(self, monkeypatch, caplog):
        """A genuine failure (outage, permission, disk issue) must be surfaced
        via logging rather than silently passed, per issue #37."""
        fake_client = MagicMock()
        fake_client.delete_collection.side_effect = RuntimeError("connection refused")
        monkeypatch.setattr(chroma_client, "get_chroma", lambda: fake_client)

        with caplog.at_level(logging.WARNING, logger="backend.database.chroma_client"):
            chroma_client.delete_chroma_collection("some-collection-id")

        assert len(caplog.records) == 1
        msg = caplog.records[0].getMessage()
        assert "some-collection-id" in msg
        assert "connection refused" in msg

    def test_successful_delete_does_not_log(self, monkeypatch, caplog):
        fake_client = MagicMock()
        monkeypatch.setattr(chroma_client, "get_chroma", lambda: fake_client)

        with caplog.at_level(logging.WARNING, logger="backend.database.chroma_client"):
            chroma_client.delete_chroma_collection("some-collection-id")

        assert caplog.records == []
