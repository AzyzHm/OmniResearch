import backend.services.rag_retrieval as rag_retrieval
from backend.tests.conftest import FakeDB


class _FakeSparseVector:
    def __init__(self, indices, values):
        self.indices = indices
        self.values = values


class _FakeChromaCollection:
    """Stand-in for a Chroma collection supporting .get() (plain fetch) and
    .query() (vector search), each returning canned results."""
    def __init__(self, get_result=None, query_result=None):
        self._get_result = get_result or {"documents": [], "metadatas": []}
        self._query_result = query_result or {"documents": [[]], "metadatas": [[]], "distances": [[]]}
        self.get_calls = []
        self.query_calls = []

    def get(self, **kwargs):
        self.get_calls.append(kwargs)
        return self._get_result

    def query(self, **kwargs):
        self.query_calls.append(kwargs)
        return self._query_result


# ---------------------------------------------------------------------------
# get_active_items_by_collection
# ---------------------------------------------------------------------------

class TestGetActiveItemsByCollection:
    def test_no_collections_returns_empty_dict(self, monkeypatch):
        db = FakeDB()
        db.add_result(data=[])
        monkeypatch.setattr(rag_retrieval, "get_supabase", lambda: db)
        assert rag_retrieval.get_active_items_by_collection("proj-1") == {}

    def test_groups_items_by_collection_id(self, monkeypatch):
        db = FakeDB()
        db.add_result(data=[{"id": "col-1"}, {"id": "col-2"}])
        db.add_result(data=[
            {"id": "item-1", "collection_id": "col-1"},
            {"id": "item-2", "collection_id": "col-1"},
            {"id": "item-3", "collection_id": "col-2"},
        ])
        monkeypatch.setattr(rag_retrieval, "get_supabase", lambda: db)

        result = rag_retrieval.get_active_items_by_collection("proj-1")

        assert result == {
            "col-1": ["item-1", "item-2"],
            "col-2": ["item-3"],
        }

    def test_skips_items_query_when_no_collections_exist(self, monkeypatch):
        """Only one DB call should happen if the project has zero collections."""
        calls = []

        class _CountingDB(FakeDB):
            def table(self, name):
                calls.append(name)
                return super().table(name)

        db = _CountingDB()
        db.add_result(data=[])
        monkeypatch.setattr(rag_retrieval, "get_supabase", lambda: db)
        rag_retrieval.get_active_items_by_collection("proj-1")
        assert calls == ["collections"]


# ---------------------------------------------------------------------------
# _fetch_all_active_chunks
# ---------------------------------------------------------------------------

class TestFetchAllActiveChunks:
    def test_no_active_items_returns_empty(self, monkeypatch):
        monkeypatch.setattr(rag_retrieval, "get_active_items_by_collection", lambda pid: {})
        assert rag_retrieval._fetch_all_active_chunks("proj-1") == []

    def test_builds_chunks_with_bm25_metadata(self, monkeypatch):
        monkeypatch.setattr(
            rag_retrieval, "get_active_items_by_collection",
            lambda pid: {"col-1": ["item-1"]},
        )
        fake_collection = _FakeChromaCollection(get_result={
            "documents": ["chunk text"],
            "metadatas": [{"source_name": "doc.pdf", "item_id": "item-1",
                            "bm25_indices": "[1, 2]", "bm25_values": "[0.5, 0.5]"}],
        })
        monkeypatch.setattr(rag_retrieval, "get_chroma_collection", lambda cid: fake_collection)

        chunks = rag_retrieval._fetch_all_active_chunks("proj-1")

        assert len(chunks) == 1
        assert chunks[0]["content"] == "chunk text"
        assert chunks[0]["source_name"] == "doc.pdf"
        assert chunks[0]["_bm25_indices"] == [1, 2]
        assert chunks[0]["_bm25_values"] == [0.5, 0.5]

    def test_missing_source_name_defaults_to_unknown(self, monkeypatch):
        monkeypatch.setattr(
            rag_retrieval, "get_active_items_by_collection",
            lambda pid: {"col-1": ["item-1"]},
        )
        fake_collection = _FakeChromaCollection(get_result={
            "documents": ["chunk text"], "metadatas": [{}],
        })
        monkeypatch.setattr(rag_retrieval, "get_chroma_collection", lambda cid: fake_collection)
        chunks = rag_retrieval._fetch_all_active_chunks("proj-1")
        assert chunks[0]["source_name"] == "unknown source"

    def test_collection_error_is_skipped_not_raised(self, monkeypatch):
        """If a chroma collection can't be opened (e.g. it was deleted), that
        collection's chunks are silently skipped rather than failing retrieval."""
        monkeypatch.setattr(
            rag_retrieval, "get_active_items_by_collection",
            lambda pid: {"col-1": ["item-1"], "col-2": ["item-2"]},
        )
        good_collection = _FakeChromaCollection(get_result={
            "documents": ["ok"], "metadatas": [{"item_id": "item-2"}],
        })

        def _get_chroma(cid):
            if cid == "col-1":
                raise Exception("collection missing")
            return good_collection

        monkeypatch.setattr(rag_retrieval, "get_chroma_collection", _get_chroma)
        chunks = rag_retrieval._fetch_all_active_chunks("proj-1")
        assert len(chunks) == 1
        assert chunks[0]["content"] == "ok"


# ---------------------------------------------------------------------------
# _retrieve_pool_semantic
# ---------------------------------------------------------------------------

class TestRetrievePoolSemantic:
    def test_no_active_items_returns_empty(self, monkeypatch):
        monkeypatch.setattr(rag_retrieval, "get_active_items_by_collection", lambda pid: {})
        assert rag_retrieval._retrieve_pool_semantic("proj-1", "q", 10) == []

    def test_sorts_by_distance_ascending_and_truncates_to_pool_size(self, monkeypatch):
        monkeypatch.setattr(
            rag_retrieval, "get_active_items_by_collection",
            lambda pid: {"col-1": ["item-1", "item-2", "item-3"]},
        )
        monkeypatch.setattr(rag_retrieval, "embed_texts", lambda texts: [[0.1, 0.2]])
        fake_collection = _FakeChromaCollection(query_result={
            "documents": [["far", "near", "middle"]],
            "metadatas": [[{"item_id": "1"}, {"item_id": "2"}, {"item_id": "3"}]],
            "distances": [[0.9, 0.1, 0.5]],
        })
        monkeypatch.setattr(rag_retrieval, "get_chroma_collection", lambda cid: fake_collection)

        pool = rag_retrieval._retrieve_pool_semantic("proj-1", "q", pool_size=2)

        assert len(pool) == 2
        assert [c["content"] for c in pool] == ["near", "middle"]

    def test_embeds_query_exactly_once(self, monkeypatch):
        monkeypatch.setattr(
            rag_retrieval, "get_active_items_by_collection",
            lambda pid: {"col-1": ["item-1"], "col-2": ["item-2"]},
        )
        embed_calls = []
        monkeypatch.setattr(
            rag_retrieval, "embed_texts",
            lambda texts: embed_calls.append(texts) or [[0.1, 0.2]],
        )
        monkeypatch.setattr(rag_retrieval, "get_chroma_collection", lambda cid: _FakeChromaCollection())
        rag_retrieval._retrieve_pool_semantic("proj-1", "my query", pool_size=5)
        assert embed_calls == [["my query"]]


# ---------------------------------------------------------------------------
# _retrieve_pool_keyword
# ---------------------------------------------------------------------------

class TestRetrievePoolKeyword:
    def test_no_chunks_returns_empty(self, monkeypatch):
        monkeypatch.setattr(rag_retrieval, "_fetch_all_active_chunks", lambda pid: [])
        assert rag_retrieval._retrieve_pool_keyword("proj-1", "q", 10) == []

    def test_filters_out_zero_score_chunks(self, monkeypatch):
        chunks = [
            {"content": "matches", "source_name": "s", "collection_id": "c", "item_id": "i1",
             "_bm25_indices": [1], "_bm25_values": [1.0]},
            {"content": "no overlap", "source_name": "s", "collection_id": "c", "item_id": "i2",
             "_bm25_indices": [99], "_bm25_values": [1.0]},
        ]
        monkeypatch.setattr(rag_retrieval, "_fetch_all_active_chunks", lambda pid: chunks)
        monkeypatch.setattr(rag_retrieval, "bm25_sparse_vector", lambda q: _FakeSparseVector([1], [1.0]))

        pool = rag_retrieval._retrieve_pool_keyword("proj-1", "q", 10)

        assert len(pool) == 1
        assert pool[0]["content"] == "matches"

    def test_higher_score_sorts_first(self, monkeypatch):
        chunks = [
            {"content": "weak match", "source_name": "s", "collection_id": "c", "item_id": "i1",
             "_bm25_indices": [1], "_bm25_values": [0.1]},
            {"content": "strong match", "source_name": "s", "collection_id": "c", "item_id": "i2",
             "_bm25_indices": [1], "_bm25_values": [0.9]},
        ]
        monkeypatch.setattr(rag_retrieval, "_fetch_all_active_chunks", lambda pid: chunks)
        monkeypatch.setattr(rag_retrieval, "bm25_sparse_vector", lambda q: _FakeSparseVector([1], [1.0]))

        pool = rag_retrieval._retrieve_pool_keyword("proj-1", "q", 10)
        assert [c["content"] for c in pool] == ["strong match", "weak match"]

    def test_truncates_to_pool_size(self, monkeypatch):
        chunks = [
            {"content": str(i), "source_name": "s", "collection_id": "c", "item_id": str(i),
             "_bm25_indices": [1], "_bm25_values": [float(i)]}
            for i in range(5)
        ]
        monkeypatch.setattr(rag_retrieval, "_fetch_all_active_chunks", lambda pid: chunks)
        monkeypatch.setattr(rag_retrieval, "bm25_sparse_vector", lambda q: _FakeSparseVector([1], [1.0]))

        pool = rag_retrieval._retrieve_pool_keyword("proj-1", "q", pool_size=2)
        assert len(pool) == 2


# ---------------------------------------------------------------------------
# _retrieve_pool_hybrid
# ---------------------------------------------------------------------------

class TestRetrievePoolHybrid:
    def test_calls_both_semantic_and_keyword_with_double_pool_size(self, monkeypatch):
        calls = {}

        def _fake_semantic(pid, q, size):
            calls["semantic"] = size
            return []

        def _fake_keyword(pid, q, size):
            calls["keyword"] = size
            return []

        monkeypatch.setattr(rag_retrieval, "_retrieve_pool_semantic", _fake_semantic)
        monkeypatch.setattr(rag_retrieval, "_retrieve_pool_keyword", _fake_keyword)
        rag_retrieval._retrieve_pool_hybrid("proj-1", "q", pool_size=10)
        assert calls == {"semantic": 20, "keyword": 20}

    def test_chunk_found_in_both_rankings_scores_higher_than_single_ranking(self, monkeypatch):
        shared_chunk = {"content": "shared", "collection_id": "c", "item_id": "1"}
        semantic_only = {"content": "semantic only", "collection_id": "c", "item_id": "2"}

        monkeypatch.setattr(
            rag_retrieval, "_retrieve_pool_semantic",
            lambda pid, q, size: [shared_chunk, semantic_only],
        )
        monkeypatch.setattr(
            rag_retrieval, "_retrieve_pool_keyword",
            lambda pid, q, size: [shared_chunk],
        )

        pool = rag_retrieval._retrieve_pool_hybrid("proj-1", "q", pool_size=10)

        assert pool[0]["content"] == "shared"  # found by both -> highest RRF score

    def test_deduplicates_the_same_chunk_across_rankings(self, monkeypatch):
        shared_chunk = {"content": "shared", "collection_id": "c", "item_id": "1"}
        monkeypatch.setattr(
            rag_retrieval, "_retrieve_pool_semantic", lambda pid, q, size: [shared_chunk],
        )
        monkeypatch.setattr(
            rag_retrieval, "_retrieve_pool_keyword", lambda pid, q, size: [dict(shared_chunk)],
        )
        pool = rag_retrieval._retrieve_pool_hybrid("proj-1", "q", pool_size=10)
        assert len(pool) == 1

    def test_truncates_to_pool_size(self, monkeypatch):
        semantic_chunks = [
            {"content": str(i), "collection_id": "c", "item_id": str(i)} for i in range(10)
        ]
        monkeypatch.setattr(
            rag_retrieval, "_retrieve_pool_semantic", lambda pid, q, size: semantic_chunks,
        )
        monkeypatch.setattr(rag_retrieval, "_retrieve_pool_keyword", lambda pid, q, size: [])
        pool = rag_retrieval._retrieve_pool_hybrid("proj-1", "q", pool_size=3)
        assert len(pool) == 3


# ---------------------------------------------------------------------------
# retrieve_pool (dispatcher)
# ---------------------------------------------------------------------------

class TestRetrievePoolDispatcher:
    def test_semantic_mode_calls_semantic_strategy(self, monkeypatch):
        monkeypatch.setattr(rag_retrieval, "_retrieve_pool_semantic", lambda pid, q, size: ["semantic"])
        monkeypatch.setattr(rag_retrieval, "_retrieve_pool_keyword", lambda pid, q, size: ["keyword"])
        monkeypatch.setattr(rag_retrieval, "_retrieve_pool_hybrid", lambda pid, q, size: ["hybrid"])
        assert rag_retrieval.retrieve_pool("p", "q", mode="semantic") == ["semantic"]

    def test_keyword_mode_calls_keyword_strategy(self, monkeypatch):
        monkeypatch.setattr(rag_retrieval, "_retrieve_pool_semantic", lambda pid, q, size: ["semantic"])
        monkeypatch.setattr(rag_retrieval, "_retrieve_pool_keyword", lambda pid, q, size: ["keyword"])
        monkeypatch.setattr(rag_retrieval, "_retrieve_pool_hybrid", lambda pid, q, size: ["hybrid"])
        assert rag_retrieval.retrieve_pool("p", "q", mode="keyword") == ["keyword"]

    def test_hybrid_mode_calls_hybrid_strategy(self, monkeypatch):
        monkeypatch.setattr(rag_retrieval, "_retrieve_pool_semantic", lambda pid, q, size: ["semantic"])
        monkeypatch.setattr(rag_retrieval, "_retrieve_pool_keyword", lambda pid, q, size: ["keyword"])
        monkeypatch.setattr(rag_retrieval, "_retrieve_pool_hybrid", lambda pid, q, size: ["hybrid"])
        assert rag_retrieval.retrieve_pool("p", "q", mode="hybrid") == ["hybrid"]

    def test_defaults_to_semantic_mode(self, monkeypatch):
        monkeypatch.setattr(rag_retrieval, "_retrieve_pool_semantic", lambda pid, q, size: ["semantic"])
        assert rag_retrieval.retrieve_pool("p", "q") == ["semantic"]