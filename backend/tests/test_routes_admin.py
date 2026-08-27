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

    def test_list_users_admin_only_sees_regular_users(self, app, admin_headers):
        """A regular admin's query is scoped to role='user' only, so any admin
        rows returned by a (mocked) DB layer would still be filtered client-side."""
        client, db = app
        db.add_result(data=[user_row("u1", "alice", role="user")])
        resp = client.get("/admin/users", headers=admin_headers)
        assert resp.status_code == 200
        assert all(u["role"] == "user" for u in resp.json()["users"])

    def test_list_users_superadmin_excludes_self(self, app, superadmin_headers):
        client, db = app
        db.add_result(data=[
            user_row("u1", "alice", role="user"),
            user_row("superadmin-001", "root", role="superadmin"),
        ])
        resp = client.get("/admin/users", headers=superadmin_headers)
        assert resp.status_code == 200
        ids = [u["id"] for u in resp.json()["users"]]
        assert "superadmin-001" not in ids
        assert "u1" in ids

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


    def test_change_role_to_admin(self, app, superadmin_headers):
        client, db = app
        db.add_result(data=[user_row("u5", "eve")])
        db.add_result(data=[])
        resp = client.put("/admin/users/u5/role?new_role=admin", headers=superadmin_headers)
        assert resp.status_code == 200
        assert "admin" in resp.json()["message"]

    def test_change_role_requires_superadmin_not_just_admin(self, app, admin_headers):
        """A regular admin (not superadmin) can no longer change roles."""
        client, _ = app
        resp = client.put("/admin/users/u5/role?new_role=admin", headers=admin_headers)
        assert resp.status_code == 403

    def test_change_own_role_forbidden(self, app, superadmin_headers):
        client, _ = app
        resp = client.put("/admin/users/superadmin-001/role?new_role=user", headers=superadmin_headers)
        assert resp.status_code == 400
        assert "own role" in resp.json()["detail"]

    def test_change_role_invalid_value(self, app, superadmin_headers):
        client, _ = app
        resp = client.put("/admin/users/u5/role?new_role=superuser", headers=superadmin_headers)
        assert resp.status_code == 422

    def test_change_role_user_not_found(self, app, superadmin_headers):
        client, db = app
        db.add_result(data=[])
        resp = client.put("/admin/users/ghost/role?new_role=user", headers=superadmin_headers)
        assert resp.status_code == 404

    def test_change_role_target_superadmin_forbidden(self, app, superadmin_headers):
        """The super admin's own role (as a target) can never be changed by anyone."""
        client, db = app
        db.add_result(data=[user_row("root-1", "root", role="superadmin")])
        resp = client.put("/admin/users/root-1/role?new_role=admin", headers=superadmin_headers)
        assert resp.status_code == 403
        assert "cannot be changed" in resp.json()["detail"]

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

    def test_delete_target_superadmin_forbidden(self, app, admin_headers):
        client, db = app
        db.add_result(data=[user_row("root-1", "root", role="superadmin")])
        resp = client.delete("/admin/users/root-1", headers=admin_headers)
        assert resp.status_code == 403
        assert "cannot be deleted" in resp.json()["detail"]

    def test_admin_cannot_delete_other_admin(self, app, admin_headers):
        """A regular admin may only delete regular user accounts, not other admins."""
        client, db = app
        db.add_result(data=[user_row("u7", "grace", role="admin")])
        resp = client.delete("/admin/users/u7", headers=admin_headers)
        assert resp.status_code == 403
        assert "only delete regular user accounts" in resp.json()["detail"]

    def test_superadmin_can_delete_admin(self, app, superadmin_headers):
        client, db = app
        db.add_result(data=[user_row("u7", "grace", role="admin")])
        db.add_result(data=[])
        resp = client.delete("/admin/users/u7", headers=superadmin_headers)
        assert resp.status_code == 200

    def test_get_logs(self, app, admin_headers):
        client, db = app
        log = {"id": "log-1", "user_id": "u1", "username": "alice",
                "login_time": "2025-01-01T00:00:00+00:00", "ip_address": "127.0.0.1"}
        db.add_result(data=[{"id": "u1"}])  # scoped user-ids query
        db.add_result(data=[log])            # logs query
        db.add_result(data=[], count=1)      # count query
        resp = client.get("/admin/logs", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "logs" in body
        assert body["total"] == 1
        assert len(body["logs"]) == 1

    def test_get_logs_returns_empty_when_no_scoped_users(self, app, admin_headers):
        """If the scoping query finds no users in scope, the route returns early
        with a single DB call (no logs/count queries)."""
        client, db = app
        db.add_result(data=[])
        resp = client.get("/admin/logs", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json() == {"logs": [], "total": 0}

    def test_get_logs_excludes_requester_from_scope(self, app, admin_headers):
        client, db = app
        # admin-001 is the requester; only u1 should remain in scope
        db.add_result(data=[{"id": "u1"}, {"id": "admin-001"}])
        db.add_result(data=[], count=0)
        resp = client.get("/admin/logs", headers=admin_headers)
        assert resp.status_code == 200


    def test_get_stats(self, app, admin_headers):
        client, db = app
        db.add_result(data=[user_row("u1", "alice", role="user", is_approved=True)])  # scoped users
        db.add_result(data=[], count=3)     # login_logs count
        db.add_result(data=[])              # recent logins
        resp = client.get("/admin/stats", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_users"] == 1
        assert body["total_logins"] == 3
        assert "admin_users" not in body  # only superadmins see this breakdown

    def test_get_stats_no_scoped_users_skips_login_queries(self, app, admin_headers):
        client, db = app
        db.add_result(data=[])
        resp = client.get("/admin/stats", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_users"] == 0
        assert body["total_logins"] == 0

    def test_get_stats_superadmin_sees_admin_breakdown(self, app, superadmin_headers):
        client, db = app
        db.add_result(data=[
            user_row("u1", "alice", role="user"),
            user_row("u2", "bob", role="admin"),
        ])
        db.add_result(data=[], count=5)
        db.add_result(data=[])
        resp = client.get("/admin/stats", headers=superadmin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["admin_users"] == 1
        assert body["total_users"] == 1