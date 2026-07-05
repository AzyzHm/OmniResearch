import backend.services.rag_llm as rag_llm


class _FakeGemini:
    """Records every call and returns a pre-set canned response."""
    def __init__(self, response="DIRECT"):
        self.response = response
        self.calls = []

    def __call__(self, messages, temperature=0.7, user_id=None):
        self.calls.append({"messages": messages, "temperature": temperature, "user_id": user_id})
        return self.response


def _patch_gemini(monkeypatch, response):
    fake = _FakeGemini(response)
    monkeypatch.setattr(rag_llm, "get_gemini_response", fake)
    return fake


class TestFormatHistory:
    def test_empty_history(self):
        assert rag_llm._format_history([]) == "(no prior conversation)"

    def test_formats_user_and_assistant_turns(self):
        history = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
        ]
        text = rag_llm._format_history(history)
        assert "User: Hi" in text
        assert "Assistant: Hello!" in text


class TestFormatContext:
    def test_empty_context(self):
        assert rag_llm._format_context([]) == "(no context retrieved)"

    def test_formats_chunks_with_source(self):
        chunks = [{"source_name": "doc.pdf", "content": "Some fact."}]
        text = rag_llm._format_context(chunks)
        assert "doc.pdf" in text
        assert "Some fact." in text

    def test_missing_source_name_defaults(self):
        chunks = [{"content": "No source given."}]
        text = rag_llm._format_context(chunks)
        assert "unknown source" in text


class TestDecideRetrieval:
    def test_retrieve_true_when_model_says_retrieve(self, monkeypatch):
        _patch_gemini(monkeypatch, "RETRIEVE")
        assert rag_llm.decide_retrieval([], "What does my document say?") is True

    def test_retrieve_false_when_model_says_direct(self, monkeypatch):
        _patch_gemini(monkeypatch, "DIRECT")
        assert rag_llm.decide_retrieval([], "Hello there!") is False

    def test_case_insensitive(self, monkeypatch):
        _patch_gemini(monkeypatch, "retrieve")
        assert rag_llm.decide_retrieval([], "anything") is True

    def test_user_id_passed_through(self, monkeypatch):
        fake = _patch_gemini(monkeypatch, "DIRECT")
        rag_llm.decide_retrieval([], "hi", user_id="user-42")
        assert fake.calls[0]["user_id"] == "user-42"


class TestRefineQuery:
    def test_returns_model_output(self, monkeypatch):
        _patch_gemini(monkeypatch, "standalone rewritten query")
        result = rag_llm.refine_query([], "what about it?")
        assert result == "standalone rewritten query"

    def test_falls_back_to_original_if_model_returns_blank(self, monkeypatch):
        _patch_gemini(monkeypatch, "   ")
        result = rag_llm.refine_query([], "original query")
        assert result == "original query"

    def test_uses_temperature_point_two(self, monkeypatch):
        fake = _patch_gemini(monkeypatch, "refined")
        rag_llm.refine_query([], "q")
        assert fake.calls[0]["temperature"] == 0.2


class TestValidateContext:
    def test_sufficient(self, monkeypatch):
        _patch_gemini(monkeypatch, "SUFFICIENT")
        assert rag_llm.validate_context("q", [{"content": "x"}]) is True

    def test_insufficient(self, monkeypatch):
        _patch_gemini(monkeypatch, "INSUFFICIENT")
        assert rag_llm.validate_context("q", [{"content": "x"}]) is False

    def test_case_insensitive(self, monkeypatch):
        _patch_gemini(monkeypatch, "sufficient")
        assert rag_llm.validate_context("q", []) is True


class TestGenerateAnswer:
    def test_returns_model_text(self, monkeypatch):
        _patch_gemini(monkeypatch, "Here is your answer.")
        answer = rag_llm.generate_answer(history=[], query="q", context_chunks=[])
        assert answer == "Here is your answer."

    def test_appends_prompt_after_history(self, monkeypatch):
        fake = _patch_gemini(monkeypatch, "answer")
        history = [{"role": "user", "content": "earlier"}]
        rag_llm.generate_answer(history=history, query="q", context_chunks=[])
        sent_messages = fake.calls[0]["messages"]
        assert sent_messages[0] == {"role": "user", "content": "earlier"}
        assert sent_messages[-1]["role"] == "user"
        assert "q" in sent_messages[-1]["content"]

    def test_uses_temperature_point_seven(self, monkeypatch):
        fake = _patch_gemini(monkeypatch, "answer")
        rag_llm.generate_answer(history=[], query="q", context_chunks=[])
        assert fake.calls[0]["temperature"] == 0.7

    def test_no_context_message_included_when_chunks_empty(self, monkeypatch):
        fake = _patch_gemini(monkeypatch, "answer")
        rag_llm.generate_answer(history=[], query="q", context_chunks=[])
        prompt = fake.calls[0]["messages"][-1]["content"]
        assert "no additional context" in prompt