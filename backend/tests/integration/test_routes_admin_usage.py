class TestGetLLMUsage:
    def test_aggregates_per_user_across_providers(self, app, admin_headers):
        client, db = app
        db.add_result(data=[
            {"id": "u1", "username": "alice"},
            {"id": "u2", "username": "bob"},
        ])
        db.add_result(data=[
            {"user_id": "u1", "provider": "gemini", "prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            {"user_id": "u1", "provider": "mistral", "prompt_tokens": 8, "completion_tokens": 4, "total_tokens": 12},
            {"user_id": "u2", "provider": "gemini", "prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30},
        ])
        resp = client.get("/admin/usage/llm", headers=admin_headers)
        assert resp.status_code == 200
        rows = {r["user_id"]: r for r in resp.json()["users"]}

        assert rows["u1"]["gemini_calls"] == 1
        assert rows["u1"]["gemini_tokens"] == 15
        assert rows["u1"]["mistral_calls"] == 1
        assert rows["u1"]["mistral_tokens"] == 12
        assert rows["u1"]["total_calls"] == 2
        assert rows["u1"]["total_tokens"] == 27

        assert rows["u2"]["gemini_calls"] == 1
        assert rows["u2"]["total_tokens"] == 30

    def test_sorted_by_total_tokens_descending(self, app, admin_headers):
        client, db = app
        db.add_result(data=[{"id": "u1", "username": "alice"}, {"id": "u2", "username": "bob"}])
        db.add_result(data=[
            {"user_id": "u1", "provider": "gemini", "prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 5},
            {"user_id": "u2", "provider": "gemini", "prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 50},
        ])
        resp = client.get("/admin/usage/llm", headers=admin_headers)
        rows = resp.json()["users"]
        assert rows[0]["user_id"] == "u2"  # higher total_tokens first

    def test_empty_usage_returns_empty_list(self, app, admin_headers):
        client, db = app
        db.add_result(data=[])
        db.add_result(data=[])
        resp = client.get("/admin/usage/llm", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["users"] == []

    def test_unknown_user_id_falls_back_to_unknown_username(self, app, admin_headers):
        client, db = app
        db.add_result(data=[])  # no users found
        db.add_result(data=[
            {"user_id": "ghost", "provider": "gemini", "prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        ])
        resp = client.get("/admin/usage/llm", headers=admin_headers)
        assert resp.json()["users"][0]["username"] == "Unknown"

    def test_requires_admin(self, app, user_headers):
        client, _ = app
        resp = client.get("/admin/usage/llm", headers=user_headers)
        assert resp.status_code == 403

    def test_unauthenticated(self, app):
        client, _ = app
        resp = client.get("/admin/usage/llm")
        assert resp.status_code in (401, 403)


class TestGetSearchUsage:
    def test_aggregates_per_user_across_engines(self, app, admin_headers):
        client, db = app
        db.add_result(data=[{"id": "u1", "username": "alice"}])
        db.add_result(data=[
            {"user_id": "u1", "engine": "tavily", "num_results": 5, "credits": 2},
            {"user_id": "u1", "engine": "tavily", "num_results": 5, "credits": 1},
            {"user_id": "u1", "engine": "exa", "num_results": 3, "credits": 1},
        ])
        resp = client.get("/admin/usage/search", headers=admin_headers)
        assert resp.status_code == 200
        row = resp.json()["users"][0]
        assert row["tavily_calls"] == 2
        assert row["tavily_credits"] == 3
        assert row["exa_calls"] == 1
        assert row["exa_credits"] == 1
        assert row["total_calls"] == 3
        assert row["total_credits"] == 4

    def test_sorted_by_total_credits_descending(self, app, admin_headers):
        client, db = app
        db.add_result(data=[{"id": "u1", "username": "alice"}, {"id": "u2", "username": "bob"}])
        db.add_result(data=[
            {"user_id": "u1", "engine": "exa", "num_results": 1, "credits": 1},
            {"user_id": "u2", "engine": "tavily", "num_results": 1, "credits": 10},
        ])
        resp = client.get("/admin/usage/search", headers=admin_headers)
        rows = resp.json()["users"]
        assert rows[0]["user_id"] == "u2"

    def test_empty_usage_returns_empty_list(self, app, admin_headers):
        client, db = app
        db.add_result(data=[])
        db.add_result(data=[])
        resp = client.get("/admin/usage/search", headers=admin_headers)
        assert resp.json()["users"] == []

    def test_requires_admin(self, app, user_headers):
        client, _ = app
        resp = client.get("/admin/usage/search", headers=user_headers)
        assert resp.status_code == 403

    def test_unauthenticated(self, app):
        client, _ = app
        resp = client.get("/admin/usage/search")
        assert resp.status_code in (401, 403)