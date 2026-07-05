import backend.routes.search as r_search


class TestSearchWebRoute:
    def test_success_returns_results(self, app, user_headers, monkeypatch):
        client, db = app
        monkeypatch.setattr(
            r_search, "search_web",
            lambda **kw: [{"url": "https://example.com", "title": "Example", "content": "Some content"}],
        )
        resp = client.post(
            "/search/web",
            json={"engine": "tavily", "query": "python testing", "num_results": 5},
            headers=user_headers,
        )
        assert resp.status_code == 200
        results = resp.json()["results"]
        assert len(results) == 1
        assert results[0]["url"] == "https://example.com"

    def test_empty_results(self, app, user_headers, monkeypatch):
        client, db = app
        monkeypatch.setattr(r_search, "search_web", lambda **kw: [])
        resp = client.post(
            "/search/web",
            json={"engine": "exa", "query": "nonexistent topic xyz"},
            headers=user_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["results"] == []

    def test_search_failure_returns_502(self, app, user_headers, monkeypatch):
        client, db = app

        def _boom(**kw):
            raise RuntimeError("Tavily API down")

        monkeypatch.setattr(r_search, "search_web", _boom)
        resp = client.post(
            "/search/web",
            json={"engine": "tavily", "query": "python testing"},
            headers=user_headers,
        )
        assert resp.status_code == 502
        assert "Search error" in resp.json()["detail"]

    def test_empty_query_rejected(self, app, user_headers):
        client, _ = app
        resp = client.post(
            "/search/web",
            json={"engine": "tavily", "query": "   "},
            headers=user_headers,
        )
        assert resp.status_code == 422

    def test_invalid_engine_rejected(self, app, user_headers):
        client, _ = app
        resp = client.post(
            "/search/web",
            json={"engine": "google", "query": "python testing"},
            headers=user_headers,
        )
        assert resp.status_code == 422

    def test_records_search_usage_on_success(self, app, user_headers, monkeypatch):
        client, db = app
        monkeypatch.setattr(r_search, "search_web", lambda **kw: [])

        recorded = []
        monkeypatch.setattr(
            r_search, "record_search_usage",
            lambda **kw: recorded.append(kw),
        )
        resp = client.post(
            "/search/web",
            json={"engine": "tavily", "query": "python", "num_results": 3, "search_depth": "advanced"},
            headers=user_headers,
        )
        assert resp.status_code == 200
        assert len(recorded) == 1
        assert recorded[0]["engine"] == "tavily"
        assert recorded[0]["search_depth"] == "advanced"
        assert recorded[0]["user_id"] == "user-123"

    def test_usage_not_recorded_on_failure(self, app, user_headers, monkeypatch):
        client, db = app

        def _boom(**kw):
            raise RuntimeError("down")

        monkeypatch.setattr(r_search, "search_web", _boom)
        recorded = []
        monkeypatch.setattr(r_search, "record_search_usage", lambda **kw: recorded.append(kw))

        resp = client.post(
            "/search/web",
            json={"engine": "exa", "query": "python"},
            headers=user_headers,
        )
        assert resp.status_code == 502
        assert not recorded

    def test_unauthenticated(self, app):
        client, _ = app
        resp = client.post("/search/web", json={"engine": "tavily", "query": "python"})
        assert resp.status_code in (401, 403)