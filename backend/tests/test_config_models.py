import pytest
import backend.config.models as models_mod
from backend.config.settings import get_settings


@pytest.fixture(autouse=True)
def _reset_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture()
def usage_calls(monkeypatch):
    """Capture every record_llm_usage(...) call without touching the DB."""
    calls = []
    monkeypatch.setattr(
        models_mod, "record_llm_usage",
        lambda *a, **kw: calls.append((a, kw)),
    )
    return calls


class TestGeminiSuccess:
    def test_returns_gemini_text_and_records_usage(self, monkeypatch, usage_calls):
        monkeypatch.setattr(
            models_mod, "_call_gemini",
            lambda messages, temperature: ("Gemini says hi", {
                "model": "gemini-2.5-flash", "prompt_tokens": 10,
                "completion_tokens": 5, "total_tokens": 15,
            }),
        )
        result = models_mod.get_gemini_response([{"role": "user", "content": "hi"}], user_id="u1")
        assert result == "Gemini says hi"
        assert len(usage_calls) == 1
        args, kwargs = usage_calls[0]
        assert args[0] == "u1"
        assert args[1] == "gemini"


class TestGeminiFailsMistralSucceeds:
    def test_falls_back_to_mistral(self, monkeypatch, usage_calls):
        monkeypatch.setattr(
            models_mod, "_call_gemini",
            lambda messages, temperature: (_ for _ in ()).throw(RuntimeError("quota exceeded")),
        )
        monkeypatch.setattr(
            models_mod, "_call_mistral",
            lambda messages, temperature: ("Mistral says hi", {
                "model": "mistral-small-2506", "prompt_tokens": 8,
                "completion_tokens": 4, "total_tokens": 12,
            }),
        )
        result = models_mod.get_gemini_response([{"role": "user", "content": "hi"}], user_id="u2")
        assert result == "Mistral says hi"
        assert len(usage_calls) == 1
        assert usage_calls[0][0][1] == "mistral"


class TestBothProvidersFail:
    def test_raises_runtime_error_with_both_messages(self, monkeypatch, usage_calls):
        monkeypatch.setattr(
            models_mod, "_call_gemini",
            lambda messages, temperature: (_ for _ in ()).throw(RuntimeError("gemini down")),
        )
        monkeypatch.setattr(
            models_mod, "_call_mistral",
            lambda messages, temperature: (_ for _ in ()).throw(RuntimeError("mistral down")),
        )
        with pytest.raises(RuntimeError) as exc_info:
            models_mod.get_gemini_response([{"role": "user", "content": "hi"}])
        assert "gemini down" in str(exc_info.value)
        assert "mistral down" in str(exc_info.value)
        assert not usage_calls  # no usage should be recorded on total failure


class TestForceMistral:
    def test_force_mistral_skips_gemini_entirely(self, monkeypatch, usage_calls):
        import os
        os.environ["FORCE_MISTRAL"] = "true"
        get_settings.cache_clear()

        gemini_called = []
        monkeypatch.setattr(
            models_mod, "_call_gemini",
            lambda messages, temperature: gemini_called.append(True),
        )
        monkeypatch.setattr(
            models_mod, "_call_mistral",
            lambda messages, temperature: ("Forced Mistral reply", {
                "model": "mistral-small-2506", "prompt_tokens": 1,
                "completion_tokens": 1, "total_tokens": 2,
            }),
        )
        result = models_mod.get_gemini_response([{"role": "user", "content": "hi"}])
        assert result == "Forced Mistral reply"
        assert not gemini_called

        os.environ["FORCE_MISTRAL"] = "false"
        get_settings.cache_clear()