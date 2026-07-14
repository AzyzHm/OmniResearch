from datetime import datetime, timezone

import backend.services.quota as quota
from backend.tests.conftest import FakeDB


class TestGetDailyTokenLimit:
    def test_returns_configured_limit(self, monkeypatch):
        db = FakeDB()
        db.add_result(data=[{"daily_token_limit": 5000}])
        monkeypatch.setattr(quota, "get_supabase", lambda: db)
        assert quota.get_daily_token_limit("u1") == 5000

    def test_falls_back_to_default_when_no_row(self, monkeypatch):
        db = FakeDB()
        db.add_result(data=[])
        monkeypatch.setattr(quota, "get_supabase", lambda: db)
        assert quota.get_daily_token_limit("ghost") == quota.DEFAULT_DAILY_TOKEN_LIMIT

    def test_falls_back_to_default_when_column_is_null(self, monkeypatch):
        db = FakeDB()
        db.add_result(data=[{"daily_token_limit": None}])
        monkeypatch.setattr(quota, "get_supabase", lambda: db)
        assert quota.get_daily_token_limit("u1") == quota.DEFAULT_DAILY_TOKEN_LIMIT

    def test_zero_limit_column_falls_back_to_default(self, monkeypatch):
        """0 is falsy, so `... or DEFAULT` treats an explicit 0 limit the same
        as a missing one — this documents that current behavior."""
        db = FakeDB()
        db.add_result(data=[{"daily_token_limit": 0}])
        monkeypatch.setattr(quota, "get_supabase", lambda: db)
        assert quota.get_daily_token_limit("u1") == quota.DEFAULT_DAILY_TOKEN_LIMIT


class TestGetTokensUsedToday:
    def test_sums_total_tokens_across_rows(self, monkeypatch):
        db = FakeDB()
        db.add_result(data=[{"total_tokens": 100}, {"total_tokens": 250}])
        monkeypatch.setattr(quota, "get_supabase", lambda: db)
        assert quota.get_tokens_used_today("u1") == 350

    def test_returns_zero_when_no_rows(self, monkeypatch):
        db = FakeDB()
        db.add_result(data=[])
        monkeypatch.setattr(quota, "get_supabase", lambda: db)
        assert quota.get_tokens_used_today("u1") == 0

    def test_treats_missing_or_null_total_tokens_as_zero(self, monkeypatch):
        db = FakeDB()
        db.add_result(data=[{"total_tokens": None}, {}, {"total_tokens": 50}])
        monkeypatch.setattr(quota, "get_supabase", lambda: db)
        assert quota.get_tokens_used_today("u1") == 50

    def test_none_data_from_db_treated_as_empty(self, monkeypatch):
        class _NoneDataResult:
            data = None
        class _NoneDataQuery:
            def __getattr__(self, name):
                return lambda *a, **kw: self
            def execute(self):
                return _NoneDataResult()
        class _NoneDataDB:
            def table(self, _name):
                return _NoneDataQuery()
        monkeypatch.setattr(quota, "get_supabase", lambda: _NoneDataDB())
        assert quota.get_tokens_used_today("u1") == 0


class TestEnforceDailyQuota:
    def test_noop_when_user_id_is_none(self, monkeypatch):
        called = []
        monkeypatch.setattr(quota, "get_supabase", lambda: called.append(True))
        quota.enforce_daily_quota(None)
        assert not called

    def test_passes_when_under_limit(self, monkeypatch):
        monkeypatch.setattr(quota, "get_daily_token_limit", lambda uid: 1000)
        monkeypatch.setattr(quota, "get_tokens_used_today", lambda uid: 500)
        quota.enforce_daily_quota("u1")

    def test_raises_when_used_equals_limit(self, monkeypatch):
        monkeypatch.setattr(quota, "get_daily_token_limit", lambda uid: 1000)
        monkeypatch.setattr(quota, "get_tokens_used_today", lambda uid: 1000)
        try:
            quota.enforce_daily_quota("u1")
            assert False, "expected DailyQuotaExceeded"
        except quota.DailyQuotaExceeded as exc:
            assert exc.used == 1000
            assert exc.limit == 1000

    def test_raises_when_used_exceeds_limit(self, monkeypatch):
        monkeypatch.setattr(quota, "get_daily_token_limit", lambda uid: 1000)
        monkeypatch.setattr(quota, "get_tokens_used_today", lambda uid: 1500)
        try:
            quota.enforce_daily_quota("u1")
            assert False, "expected DailyQuotaExceeded"
        except quota.DailyQuotaExceeded as exc:
            assert exc.used == 1500


class TestDailyQuotaExceeded:
    def test_message_includes_used_and_limit(self):
        reset_at = datetime.now(timezone.utc).replace(hour=23, minute=59, second=0, microsecond=0)
        exc = quota.DailyQuotaExceeded(used=80_000, limit=80_000, reset_at=reset_at)
        msg = str(exc)
        assert "80,000" in msg
        assert "resets at" in msg

    def test_stores_used_limit_and_reset_at_as_attributes(self):
        reset_at = datetime.now(timezone.utc)
        exc = quota.DailyQuotaExceeded(used=10, limit=20, reset_at=reset_at)
        assert exc.used == 10
        assert exc.limit == 20
        assert exc.reset_at == reset_at

    def test_time_remaining_is_never_negative_in_message(self):
        """If reset_at is (implausibly) already in the past, hours/minutes
        should clamp to 0 rather than showing a negative countdown."""
        past = datetime.now(timezone.utc).replace(year=2000)
        exc = quota.DailyQuotaExceeded(used=1, limit=1, reset_at=past)
        assert "-" not in str(exc).split("in ")[-1]