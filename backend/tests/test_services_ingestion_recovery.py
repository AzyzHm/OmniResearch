import logging

import services.ingestion_recovery as ingestion_recovery
from tests.conftest import FakeDB


class _RaisingDB:
    """A fake DB whose .table() always raises, to test the best-effort swallow."""
    def table(self, _name):
        raise ConnectionError("DB is unreachable")


class TestRecoverStuckProcessingItems:
    def test_recovers_stuck_items_and_returns_count(self, monkeypatch):
        db = FakeDB()
        db.add_result(data=[{"id": "item-1"}, {"id": "item-2"}])
        monkeypatch.setattr(ingestion_recovery, "get_supabase", lambda: db)

        recovered = ingestion_recovery.recover_stuck_processing_items()

        assert recovered == 2

    def test_no_stuck_items_returns_zero(self, monkeypatch):
        db = FakeDB()
        db.add_result(data=[])
        monkeypatch.setattr(ingestion_recovery, "get_supabase", lambda: db)

        recovered = ingestion_recovery.recover_stuck_processing_items()

        assert recovered == 0

    def test_updates_status_and_error_message(self, monkeypatch):
        captured = {}

        class _CapturingQuery:
            def update(self, payload):
                captured.update(payload)
                return self
            def eq(self, *args, **kwargs):
                return self
            def execute(self):
                return type("R", (), {"data": [{"id": "item-1"}]})()

        monkeypatch.setattr(
            ingestion_recovery, "get_supabase",
            lambda: type("D", (), {"table": lambda self, n: _CapturingQuery()})(),
        )
        ingestion_recovery.recover_stuck_processing_items()

        assert captured["status"] == "error"
        assert captured["error_message"] == ingestion_recovery.STUCK_PROCESSING_MESSAGE

    def test_filters_on_processing_status(self, monkeypatch):
        eq_calls = []

        class _CapturingQuery:
            def update(self, payload):
                return self
            def eq(self, field, value):
                eq_calls.append((field, value))
                return self
            def execute(self):
                return type("R", (), {"data": []})()

        monkeypatch.setattr(
            ingestion_recovery, "get_supabase",
            lambda: type("D", (), {"table": lambda self, n: _CapturingQuery()})(),
        )
        ingestion_recovery.recover_stuck_processing_items()

        assert ("status", "processing") in eq_calls

    def test_swallows_db_errors_and_logs(self, monkeypatch, caplog):
        monkeypatch.setattr(ingestion_recovery, "get_supabase", lambda: _RaisingDB())

        with caplog.at_level(logging.ERROR, logger="backend.services.ingestion_recovery"):
            recovered = ingestion_recovery.recover_stuck_processing_items()

        assert recovered == 0
        assert any("Failed to sweep" in r.getMessage() for r in caplog.records)

    def test_logs_warning_when_items_recovered(self, monkeypatch, caplog):
        db = FakeDB()
        db.add_result(data=[{"id": "item-1"}])
        monkeypatch.setattr(ingestion_recovery, "get_supabase", lambda: db)

        with caplog.at_level(logging.WARNING, logger="backend.services.ingestion_recovery"):
            ingestion_recovery.recover_stuck_processing_items()

        assert any("Recovered 1" in r.getMessage() for r in caplog.records)

    def test_no_log_when_nothing_recovered(self, monkeypatch, caplog):
        db = FakeDB()
        db.add_result(data=[])
        monkeypatch.setattr(ingestion_recovery, "get_supabase", lambda: db)

        with caplog.at_level(logging.WARNING, logger="backend.services.ingestion_recovery"):
            ingestion_recovery.recover_stuck_processing_items()

        assert caplog.records == []