import backend.graph.nodes.generate_node as generate_mod
import backend.graph.nodes.refine_query_node as refine_mod
import backend.graph.nodes.rerank_node as rerank_node_mod
import backend.graph.nodes.retrieve_node as retrieve_mod
import backend.graph.nodes.router_node as router_mod
import backend.graph.nodes.validation_node as validation_mod


def _base_state(**overrides):
    state = {
        "project_id": "proj-1", "chat_id": "chat-1", "user_id": "user-1",
        "query": "What is the refund policy?", "history": [], "retrieval_mode": "semantic",
    }
    state.update(overrides)
    return state


class TestRouterNode:
    def test_returns_needs_retrieval_true(self, monkeypatch):
        monkeypatch.setattr(router_mod, "decide_retrieval", lambda history, query, user_id: True)
        result = router_mod.router_node(_base_state()) # type: ignore
        assert result == {"needs_retrieval": True}

    def test_returns_needs_retrieval_false(self, monkeypatch):
        monkeypatch.setattr(router_mod, "decide_retrieval", lambda history, query, user_id: False)
        result = router_mod.router_node(_base_state()) # type: ignore
        assert result == {"needs_retrieval": False}

    def test_passes_through_query_history_and_user_id(self, monkeypatch):
        captured = {}
        def _fake(history, query, user_id):
            captured.update(history=history, query=query, user_id=user_id)
            return True
        monkeypatch.setattr(router_mod, "decide_retrieval", _fake)
        router_mod.router_node(_base_state(history=[{"role": "user", "content": "hi"}])) # type: ignore
        assert captured["query"] == "What is the refund policy?"
        assert captured["user_id"] == "user-1"
        assert captured["history"] == [{"role": "user", "content": "hi"}]


class TestRefineQueryNode:
    def test_returns_refined_query(self, monkeypatch):
        monkeypatch.setattr(refine_mod, "refine_query", lambda history, query, user_id: "refund policy details")
        result = refine_mod.refine_query_node(_base_state()) # type: ignore
        assert result == {"refined_query": "refund policy details"}


class TestRetrieveNode:
    def test_first_attempt_uses_original_query(self, monkeypatch):
        captured = {}
        def _fake_retrieve_pool(project_id, query, pool_size, mode):
            captured["query"] = query
            return [{"content": "chunk"}]
        monkeypatch.setattr(retrieve_mod, "retrieve_pool", _fake_retrieve_pool)
        result = retrieve_mod.retrieve_node(_base_state()) # type: ignore
        assert captured["query"] == "What is the refund policy?"
        assert result["retrieved_pool"] == [{"content": "chunk"}]
        assert result["retrieval_attempts"] == 1

    def test_prefers_refined_query_over_original(self, monkeypatch):
        captured = {}
        monkeypatch.setattr(
            retrieve_mod, "retrieve_pool",
            lambda project_id, query, pool_size, mode: captured.setdefault("query", query) and []
        )
        retrieve_mod.retrieve_node(_base_state(refined_query="better query")) # type: ignore
        assert captured["query"] == "better query"

    def test_prefers_missing_query_over_refined_query(self, monkeypatch):
        captured = {}
        monkeypatch.setattr(
            retrieve_mod, "retrieve_pool",
            lambda project_id, query, pool_size, mode: captured.setdefault("query", query) and []
        )
        retrieve_mod.retrieve_node(_base_state(refined_query="refined", missing_query="follow-up")) # type: ignore
        assert captured["query"] == "follow-up"

    def test_increments_retrieval_attempts(self, monkeypatch):
        monkeypatch.setattr(retrieve_mod, "retrieve_pool", lambda **kw: [])
        result = retrieve_mod.retrieve_node(_base_state(retrieval_attempts=1)) # type: ignore
        assert result["retrieval_attempts"] == 2

    def test_empty_pool_with_no_existing_context_marks_validation_passed(self, monkeypatch):
        """An empty pool with nothing accepted yet means there's truly nothing
        to retrieve — skip straight past validation instead of retrying forever."""
        monkeypatch.setattr(retrieve_mod, "retrieve_pool", lambda **kw: [])
        result = retrieve_mod.retrieve_node(_base_state()) # type: ignore
        assert result["validation_passed"] is True

    def test_empty_pool_with_existing_context_does_not_mark_validation_passed(self, monkeypatch):
        monkeypatch.setattr(retrieve_mod, "retrieve_pool", lambda **kw: [])
        result = retrieve_mod.retrieve_node(_base_state(context_chunks=[{"content": "already have this"}])) # type: ignore
        assert result["validation_passed"] is False

    def test_passes_retrieval_mode_through_to_retrieve_pool(self, monkeypatch):
        captured = {}
        monkeypatch.setattr(
            retrieve_mod, "retrieve_pool",
            lambda project_id, query, pool_size, mode: captured.setdefault("mode", mode) and []
        )
        retrieve_mod.retrieve_node(_base_state(retrieval_mode="hybrid")) # type: ignore
        assert captured["mode"] == "hybrid"


class TestRerankNode:
    def test_empty_pool_returns_existing_context_unchanged(self):
        existing = [{"content": "kept", "collection_id": "c", "item_id": "1"}]
        result = rerank_node_mod.rerank_node(_base_state(retrieved_pool=[], context_chunks=existing)) # type: ignore
        assert result == {"context_chunks": existing}

    def test_merges_reranked_chunks_into_existing_context(self, monkeypatch):
        monkeypatch.setattr(
            rerank_node_mod, "rerank",
            lambda query, pool, top_k: [{"content": "new", "collection_id": "c", "item_id": "2"}],
        )
        existing = [{"content": "old", "collection_id": "c", "item_id": "1"}]
        result = rerank_node_mod.rerank_node(
            _base_state(retrieved_pool=[{"content": "candidate"}], context_chunks=existing) # type: ignore
        )
        contents = {c["content"] for c in result["context_chunks"]}
        assert contents == {"old", "new"}

    def test_deduplicates_chunk_already_in_context(self, monkeypatch):
        dup = {"content": "same", "collection_id": "c", "item_id": "1"}
        monkeypatch.setattr(rerank_node_mod, "rerank", lambda query, pool, top_k: [dup])
        result = rerank_node_mod.rerank_node(
            _base_state(retrieved_pool=[dup], context_chunks=[dup]) # type: ignore
        )
        assert len(result["context_chunks"]) == 1

    def test_uses_missing_query_when_present(self, monkeypatch):
        captured = {}
        monkeypatch.setattr(
            rerank_node_mod, "rerank",
            lambda query, pool, top_k: captured.setdefault("query", query) and []
        )
        rerank_node_mod.rerank_node(
            _base_state(retrieved_pool=[{"content": "x"}], missing_query="follow-up") # type: ignore
        )
        assert captured["query"] == "follow-up"


class TestValidationNode:
    def test_skips_when_already_marked_passed(self):
        result = validation_mod.validation_node(_base_state(validation_passed=True)) # type: ignore
        assert result == {"validation_passed": True}

    def test_sufficient_context_passes(self, monkeypatch):
        monkeypatch.setattr(validation_mod, "validate_context", lambda query, chunks, user_id: (True, None))
        result = validation_mod.validation_node(_base_state(context_chunks=[{"content": "x"}])) # type: ignore
        assert result == {"validation_passed": True, "missing_query": None}

    def test_insufficient_context_fails_with_missing_query(self, monkeypatch):
        monkeypatch.setattr(
            validation_mod, "validate_context",
            lambda query, chunks, user_id: (False, "pricing details"),
        )
        result = validation_mod.validation_node(_base_state(context_chunks=[])) # type: ignore
        assert result == {"validation_passed": False, "missing_query": "pricing details"}


class TestGenerateNode:
    def test_generates_answer_normally(self, monkeypatch):
        monkeypatch.setattr(generate_mod, "generate_answer", lambda **kw: "The answer is 42.")
        result = generate_mod.generate_node(_base_state(context_chunks=[{"content": "x"}])) # type: ignore
        assert result == {"answer": "The answer is 42."}

    def test_retrieval_needed_but_no_chunks_returns_no_sources_message(self, monkeypatch):
        called = []
        monkeypatch.setattr(generate_mod, "generate_answer", lambda **kw: called.append(True))
        result = generate_mod.generate_node(_base_state(needs_retrieval=True, context_chunks=[])) # type: ignore
        assert result["answer"] == generate_mod.NO_SOURCES_MESSAGE
        assert not called  # the LLM should never be called in this case

    def test_no_retrieval_needed_generates_without_context(self, monkeypatch):
        """A conversational message that doesn't need retrieval should still
        get an answer even with zero context chunks."""
        monkeypatch.setattr(generate_mod, "generate_answer", lambda **kw: "Hi there!")
        result = generate_mod.generate_node(_base_state(needs_retrieval=False, context_chunks=[])) # type: ignore
        assert result == {"answer": "Hi there!"}