from backend.tests.conftest import user_row

class TestAdminRoutes:

    def test_list_users_requires_admin(self, app, user_headers):
        client, _ = app
        resp = client.get("/admin/users", headers=user_headers)
        assert resp.status_code == 403

    def test_list_users_unauthenticated(self, app):
        client, _ = app
        resp = client.get("/admin/users")
        assert resp.status_code in (401, 403)

    def test_list_users_success(self, app, admin_headers):
        client, db = app
        db.add_result(data=[user_row(), user_row("u2", "bob")])
        resp = client.get("/admin/users", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        assert len(body["users"]) == 2

    def test_list_users_pending_only(self, app, admin_headers):
        client, db = app
        db.add_result(data=[user_row("u3", "carol", is_approved=False)])
        resp = client.get("/admin/users?pending_only=true", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_approve_user_success(self, app, admin_headers):
        client, db = app
        db.add_result(data=[user_row("u3", "carol", is_approved=False)])
        db.add_result(data=[])
        resp = client.put("/admin/users/u3/approve", headers=admin_headers)
        assert resp.status_code == 200
        assert "approved" in resp.json()["message"].lower()

    def test_approve_already_approved(self, app, admin_headers):
        client, db = app
        db.add_result(data=[user_row("u4", "dave", is_approved=True)])
        resp = client.put("/admin/users/u4/approve", headers=admin_headers)
        assert resp.status_code == 200
        assert "already approved" in resp.json()["message"].lower()

    def test_approve_user_not_found(self, app, admin_headers):
        client, db = app
        db.add_result(data=[])
        resp = client.put("/admin/users/ghost/approve", headers=admin_headers)
        assert resp.status_code == 404


    def test_change_role_to_admin(self, app, admin_headers):
        client, db = app
        db.add_result(data=[user_row("u5", "eve")])
        db.add_result(data=[])
        resp = client.put("/admin/users/u5/role?new_role=admin", headers=admin_headers)
        assert resp.status_code == 200
        assert "admin" in resp.json()["message"]

    def test_change_own_role_forbidden(self, app, admin_headers):
        client, _ = app
        resp = client.put("/admin/users/admin-001/role?new_role=user", headers=admin_headers)
        assert resp.status_code == 400
        assert "own role" in resp.json()["detail"]

    def test_change_role_invalid_value(self, app, admin_headers):
        client, _ = app
        resp = client.put("/admin/users/u5/role?new_role=superuser", headers=admin_headers)
        assert resp.status_code == 422

    def test_change_role_user_not_found(self, app, admin_headers):
        client, db = app
        db.add_result(data=[])
        resp = client.put("/admin/users/ghost/role?new_role=user", headers=admin_headers)
        assert resp.status_code == 404

    def test_delete_user_success(self, app, admin_headers):
        client, db = app
        db.add_result(data=[user_row("u6", "frank")])
        db.add_result(data=[])
        resp = client.delete("/admin/users/u6", headers=admin_headers)
        assert resp.status_code == 200
        assert "deleted" in resp.json()["message"].lower()

    def test_delete_own_account_forbidden(self, app, admin_headers):
        client, _ = app
        resp = client.delete("/admin/users/admin-001", headers=admin_headers)
        assert resp.status_code == 400

    def test_delete_user_not_found(self, app, admin_headers):
        client, db = app
        db.add_result(data=[])
        resp = client.delete("/admin/users/ghost", headers=admin_headers)
        assert resp.status_code == 404

    def test_get_logs(self, app, admin_headers):
        client, db = app
        log = {"id": "log-1", "user_id": "u1", "username": "alice",
                "login_time": "2025-01-01T00:00:00+00:00", "ip_address": "127.0.0.1"}
        db.add_result(data=[log], count=1)
        db.add_result(data=[], count=1)
        resp = client.get("/admin/logs", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "logs" in body
        assert body["total"] >= 1


    def test_get_stats(self, app, admin_headers):
        client, db = app
        for _ in range(10):
            db.add_result(data=[], count=5)
        resp = client.get("/admin/stats", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "total_users" in body
        assert "total_logins" in body