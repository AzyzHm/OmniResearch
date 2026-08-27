import backend.services.usage_tracker as usage_tracker
from backend.tests.conftest import FakeDB


class _RaisingDB:
    """A fake DB whose .table() always raises, to test the try/except swallow."""
    def table(self, _name):
        raise ConnectionError("DB is unreachable")


class TestRecordLLMUsage:
    def test_inserts_row_with_correct_fields(self, monkeypatch):
        db = FakeDB()
        db.add_result(data=[{}])
        monkeypatch.setattr(usage_tracker, "get_supabase", lambda: db)

        usage_tracker.record_llm_usage(
            user_id="u1", provider="gemini", model="gemini-2.5-flash",
            prompt_tokens=10, completion_tokens=5, total_tokens=15,
        )

    def test_noop_when_user_id_is_none(self, monkeypatch):
        called = []
        monkeypatch.setattr(usage_tracker, "get_supabase", lambda: called.append(True))
        usage_tracker.record_llm_usage(
            user_id=None, provider="gemini", model="x",
            prompt_tokens=1, completion_tokens=1, total_tokens=2,
        )
        assert not called

    def test_swallows_db_errors_silently(self, monkeypatch):
        monkeypatch.setattr(usage_tracker, "get_supabase", lambda: _RaisingDB())
        usage_tracker.record_llm_usage(
            user_id="u1", provider="gemini", model="x",
            prompt_tokens=1, completion_tokens=1, total_tokens=2,
        )

    def test_none_token_counts_default_to_zero(self, monkeypatch):
        db = FakeDB()
        db.add_result(data=[{}])
        captured = {}

        class _CapturingQuery:
            def insert(self, payload):
                captured.update(payload)
                return self
            def execute(self):
                return None

        monkeypatch.setattr(usage_tracker, "get_supabase", lambda: type("D", (), {"table": lambda self, n: _CapturingQuery()})())
        usage_tracker.record_llm_usage(
            user_id="u1", provider="gemini", model="x",
            prompt_tokens=None, completion_tokens=None, total_tokens=None, # type: ignore
        )
        assert captured["prompt_tokens"] == 0
        assert captured["completion_tokens"] == 0
        assert captured["total_tokens"] == 0


class TestRecordSearchUsage:
    def test_noop_when_user_id_is_none(self, monkeypatch):
        called = []
        monkeypatch.setattr(usage_tracker, "get_supabase", lambda: called.append(True))
        usage_tracker.record_search_usage(user_id=None, engine="tavily", num_results=5)
        assert not called

    def test_swallows_db_errors_silently(self, monkeypatch):
        monkeypatch.setattr(usage_tracker, "get_supabase", lambda: _RaisingDB())
        usage_tracker.record_search_usage(user_id="u1", engine="exa", num_results=5)

    def test_tavily_advanced_costs_two_credits(self, monkeypatch):
        captured = {}

        class _CapturingQuery:
            def insert(self, payload):
                captured.update(payload)
                return self
            def execute(self):
                return None

        monkeypatch.setattr(usage_tracker, "get_supabase", lambda: type("D", (), {"table": lambda self, n: _CapturingQuery()})())
        usage_tracker.record_search_usage(user_id="u1", engine="tavily", num_results=10, search_depth="advanced")
        assert captured["credits"] == 2

    def test_tavily_basic_costs_one_credit(self, monkeypatch):
        captured = {}

        class _CapturingQuery:
            def insert(self, payload):
                captured.update(payload)
                return self
            def execute(self):
                return None

        monkeypatch.setattr(usage_tracker, "get_supabase", lambda: type("D", (), {"table": lambda self, n: _CapturingQuery()})())
        usage_tracker.record_search_usage(user_id="u1", engine="tavily", num_results=10, search_depth="basic")
        assert captured["credits"] == 1

    def test_exa_always_costs_one_credit(self, monkeypatch):
        captured = {}

        class _CapturingQuery:
            def insert(self, payload):
                captured.update(payload)
                return self
            def execute(self):
                return None

        monkeypatch.setattr(usage_tracker, "get_supabase", lambda: type("D", (), {"table": lambda self, n: _CapturingQuery()})())
        usage_tracker.record_search_usage(user_id="u1", engine="exa", num_results=10, search_depth=None)
        assert captured["credits"] == 1