from backend.config.settings import get_settings


class TestHealthEndpoint:
    def test_health_ok(self, app):
        client, _ = app
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["service"] == "OmniResearch API"
        assert isinstance(body["cors_origins"], list)

    def test_health_no_auth_required(self, app):
        """Health check must be accessible without a token."""
        client, _ = app
        resp = client.get("/health")
        assert resp.status_code == 200


class TestSettings:
    def test_cors_origins_parsed_correctly(self):
        get_settings.cache_clear()
        import os
        os.environ["CORS_ORIGINS"] = "http://localhost:8501,http://127.0.0.1:8501"
        s = get_settings()
        assert isinstance(s.cors_origins_list, list)
        for origin in s.cors_origins_list:
            assert not origin.endswith("/")

    def test_jwt_defaults(self):
        get_settings.cache_clear()
        s = get_settings()
        assert s.jwt_algorithm == "HS256"
        assert s.jwt_expire_minutes == 60

    def test_chroma_persist_dir_default(self):
        get_settings.cache_clear()
        s = get_settings()
        assert s.chroma_persist_dir == "vector_database"

    def test_retrieval_and_reranker_defaults(self):
        get_settings.cache_clear()
        s = get_settings()
        assert s.reranker_model_name == "BAAI/bge-reranker-base"
        assert s.retrieval_pool_size == 50
        assert s.rerank_top_k == 5