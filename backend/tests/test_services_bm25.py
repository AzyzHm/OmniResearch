import backend.services.bm25 as bm25


class _FakeSparseVector:
    """Stand-in for chromadb's SparseVector — just needs .indices/.values."""
    def __init__(self, indices, values):
        self.indices = indices
        self.values = values


class _FakeEmbeddingFunction:
    """Records every call and returns one canned SparseVector per input text."""
    def __init__(self, vectors=None):
        self.calls = []
        self._vectors = vectors

    def __call__(self, texts):
        self.calls.append(list(texts))
        if self._vectors is not None:
            return self._vectors
        return [_FakeSparseVector([i], [1.0]) for i in range(len(texts))]


class TestBm25SparseVector:
    def test_wraps_single_text_in_a_list_and_returns_first_result(self, monkeypatch):
        fake_ef = _FakeEmbeddingFunction(vectors=[_FakeSparseVector([1, 2], [0.5, 0.3])])
        monkeypatch.setattr(bm25, "_bm25_ef", fake_ef)

        result = bm25.bm25_sparse_vector("hello world")

        assert fake_ef.calls == [["hello world"]]
        assert result.indices == [1, 2]
        assert result.values == [0.5, 0.3]


class TestBm25SparseVectors:
    def test_empty_list_returns_empty_without_calling_ef(self, monkeypatch):
        fake_ef = _FakeEmbeddingFunction()
        monkeypatch.setattr(bm25, "_bm25_ef", fake_ef)

        assert bm25.bm25_sparse_vectors([]) == []
        assert fake_ef.calls == []  # short-circuited before touching the ef

    def test_batch_call_passes_all_texts_in_one_call(self, monkeypatch):
        fake_ef = _FakeEmbeddingFunction()
        monkeypatch.setattr(bm25, "_bm25_ef", fake_ef)

        result = bm25.bm25_sparse_vectors(["a", "b", "c"])

        assert fake_ef.calls == [["a", "b", "c"]]  # one batched call, not three
        assert len(result) == 3


class TestSparseVectorMetadataRoundTrip:
    def test_round_trip_preserves_indices_and_values(self):
        sv = _FakeSparseVector([3, 7, 12], [0.1, 0.2, 0.7])
        meta = bm25.sparse_vector_to_metadata(sv) # type: ignore
        indices, values = bm25.sparse_vector_from_metadata(meta)
        assert indices == [3, 7, 12]
        assert values == [0.1, 0.2, 0.7]

    def test_metadata_values_are_json_strings(self):
        sv = _FakeSparseVector([1], [0.9])
        meta = bm25.sparse_vector_to_metadata(sv) # type: ignore
        assert isinstance(meta["bm25_indices"], str)
        assert isinstance(meta["bm25_values"], str)

    def test_empty_sparse_vector_round_trips_to_empty_lists(self):
        sv = _FakeSparseVector([], [])
        meta = bm25.sparse_vector_to_metadata(sv) # type: ignore
        assert bm25.sparse_vector_from_metadata(meta) == ([], [])

    def test_missing_metadata_fields_default_to_empty(self):
        """Chunks stored before this feature existed have no bm25_* fields."""
        assert bm25.sparse_vector_from_metadata({}) == ([], [])

    def test_malformed_json_in_metadata_falls_back_to_empty(self):
        meta = {"bm25_indices": "not valid json", "bm25_values": "[1, 2]"}
        assert bm25.sparse_vector_from_metadata(meta) == ([], [])

    def test_none_values_in_metadata_fall_back_to_empty(self):
        meta = {"bm25_indices": None, "bm25_values": None}
        assert bm25.sparse_vector_from_metadata(meta) == ([], [])


class TestSparseDot:
    def test_no_overlap_returns_zero(self):
        assert bm25.sparse_dot([1, 2], [1.0, 1.0], [3, 4], [1.0, 1.0]) == 0.0

    def test_full_overlap_computes_weighted_sum(self):
        # query: {1: 2.0, 2: 3.0}; doc: {1: 4.0, 2: 5.0} -> 2*4 + 3*5 = 23
        result = bm25.sparse_dot([1, 2], [2.0, 3.0], [1, 2], [4.0, 5.0])
        assert result == 23.0

    def test_partial_overlap_only_scores_shared_terms(self):
        # query: {1: 2.0, 2: 3.0}; doc: {2: 5.0, 9: 1.0} -> only term 2 overlaps -> 3*5 = 15
        result = bm25.sparse_dot([1, 2], [2.0, 3.0], [2, 9], [5.0, 1.0])
        assert result == 15.0

    def test_empty_query_indices_returns_zero(self):
        assert bm25.sparse_dot([], [], [1, 2], [1.0, 1.0]) == 0.0

    def test_empty_doc_indices_returns_zero(self):
        assert bm25.sparse_dot([1, 2], [1.0, 1.0], [], []) == 0.0