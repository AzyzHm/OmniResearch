from backend.tests.conftest import user_row


class TestUpdateTokenLimit:
    def test_superadmin_or_admin_can_update_limit(self, app, admin_headers):
        client, db = app
        db.add_result(data=[user_row("u1", "alice")])   # target exists
        db.add_result(data=[])                            # update
        resp = client.put(
            "/admin/users/u1/token-limit", json={"daily_token_limit": 5000}, headers=admin_headers,
        )
        assert resp.status_code == 200
        assert "5000" in resp.json()["message"] or "5,000" in resp.json()["message"]

    def test_user_not_found_returns_404(self, app, admin_headers):
        client, db = app
        db.add_result(data=[])
        resp = client.put(
            "/admin/users/ghost/token-limit", json={"daily_token_limit": 5000}, headers=admin_headers,
        )
        assert resp.status_code == 404

    def test_negative_limit_rejected_by_validation(self, app, admin_headers):
        client, _ = app
        resp = client.put(
            "/admin/users/u1/token-limit", json={"daily_token_limit": -1}, headers=admin_headers,
        )
        assert resp.status_code == 422

    def test_over_max_limit_rejected_by_validation(self, app, admin_headers):
        client, _ = app
        resp = client.put(
            "/admin/users/u1/token-limit", json={"daily_token_limit": 100_000_001}, headers=admin_headers,
        )
        assert resp.status_code == 422

    def test_zero_limit_is_accepted_by_validation(self, app, admin_headers):
        client, db = app
        db.add_result(data=[user_row("u1", "alice")])
        db.add_result(data=[])
        resp = client.put(
            "/admin/users/u1/token-limit", json={"daily_token_limit": 0}, headers=admin_headers,
        )
        assert resp.status_code == 200

    def test_regular_user_forbidden(self, app, user_headers):
        client, _ = app
        resp = client.put(
            "/admin/users/u1/token-limit", json={"daily_token_limit": 5000}, headers=user_headers,
        )
        assert resp.status_code == 403

    def test_unauthenticated_rejected(self, app):
        client, _ = app
        resp = client.put("/admin/users/u1/token-limit", json={"daily_token_limit": 5000})
        assert resp.status_code in (401, 403)