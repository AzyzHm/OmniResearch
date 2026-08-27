import backend.services.reranker as reranker


class _FakeCrossEncoder:
    """Stand-in for sentence_transformers.CrossEncoder — scores pairs by a
    lookup table keyed on the chunk content, defaulting to 0.0."""
    def __init__(self, scores_by_content: dict):
        self._scores = scores_by_content
        self.predict_calls = []

    def predict(self, pairs):
        self.predict_calls.append(pairs)
        return [self._scores.get(content, 0.0) for _query, content in pairs]


class TestRerank:
    def test_empty_chunks_returns_empty_without_loading_model(self, monkeypatch):
        calls = []
        monkeypatch.setattr(reranker, "_get_model", lambda: calls.append(True))
        assert reranker.rerank("query", [], top_k=5) == []
        assert not calls

    def test_sorts_by_score_descending(self, monkeypatch):
        chunks = [
            {"content": "low relevance"},
            {"content": "high relevance"},
            {"content": "medium relevance"},
        ]
        fake_model = _FakeCrossEncoder({
            "low relevance": 0.1, "high relevance": 0.9, "medium relevance": 0.5,
        })
        monkeypatch.setattr(reranker, "_get_model", lambda: fake_model)

        result = reranker.rerank("query", chunks, top_k=5)

        assert [c["content"] for c in result] == [
            "high relevance", "medium relevance", "low relevance",
        ]

    def test_attaches_rerank_score_field(self, monkeypatch):
        chunks = [{"content": "a"}]
        fake_model = _FakeCrossEncoder({"a": 0.42})
        monkeypatch.setattr(reranker, "_get_model", lambda: fake_model)

        result = reranker.rerank("query", chunks, top_k=5)
        assert result[0]["rerank_score"] == 0.42

    def test_truncates_to_top_k(self, monkeypatch):
        chunks = [{"content": str(i)} for i in range(10)]
        fake_model = _FakeCrossEncoder({str(i): float(i) for i in range(10)})
        monkeypatch.setattr(reranker, "_get_model", lambda: fake_model)

        result = reranker.rerank("query", chunks, top_k=3)
        assert len(result) == 3
        assert [c["content"] for c in result] == ["9", "8", "7"]

    def test_top_k_larger_than_pool_returns_all_chunks(self, monkeypatch):
        chunks = [{"content": "only one"}]
        fake_model = _FakeCrossEncoder({"only one": 1.0})
        monkeypatch.setattr(reranker, "_get_model", lambda: fake_model)

        result = reranker.rerank("query", chunks, top_k=5)
        assert len(result) == 1

    def test_pairs_query_with_each_chunk_content(self, monkeypatch):
        chunks = [{"content": "chunk A"}, {"content": "chunk B"}]
        fake_model = _FakeCrossEncoder({})
        monkeypatch.setattr(reranker, "_get_model", lambda: fake_model)

        reranker.rerank("my query", chunks, top_k=5)

        assert fake_model.predict_calls == [[("my query", "chunk A"), ("my query", "chunk B")]]

    def test_original_chunk_fields_are_preserved(self, monkeypatch):
        chunks = [{"content": "a", "source_name": "doc.pdf", "collection_id": "c1"}]
        fake_model = _FakeCrossEncoder({"a": 1.0})
        monkeypatch.setattr(reranker, "_get_model", lambda: fake_model)

        result = reranker.rerank("q", chunks, top_k=5)
        assert result[0]["source_name"] == "doc.pdf"
        assert result[0]["collection_id"] == "c1"

    def test_does_not_mutate_the_original_chunk_dicts(self, monkeypatch):
        chunk = {"content": "a"}
        chunks = [chunk]
        fake_model = _FakeCrossEncoder({"a": 1.0})
        monkeypatch.setattr(reranker, "_get_model", lambda: fake_model)

        reranker.rerank("q", chunks, top_k=5)
        assert "rerank_score" not in chunk  # a new dict was returned, not mutated in place


class TestGetModel:
    def test_warms_up_lazily_on_first_use_and_caches(self, monkeypatch):
        warm_up_calls = []

        def _fake_warm_up():
            reranker._model = _FakeCrossEncoder({})
            warm_up_calls.append(True)

        monkeypatch.setattr(reranker, "_model", None)
        monkeypatch.setattr(reranker, "warm_up_reranker", _fake_warm_up)

        model1 = reranker._get_model()
        model2 = reranker._get_model()

        assert len(warm_up_calls) == 1  # only warmed up once
        assert model1 is model2

    def test_raises_if_warm_up_fails_to_set_a_model(self, monkeypatch):
        monkeypatch.setattr(reranker, "_model", None)
        monkeypatch.setattr(reranker, "warm_up_reranker", lambda: None)  # simulates failed load

        try:
            reranker._get_model()
            assert False, "expected RuntimeError"
        except RuntimeError as exc:
            assert "failed to load" in str(exc)