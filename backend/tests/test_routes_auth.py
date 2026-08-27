from backend.config.auth import hash_password


class TestRegister:
    def test_register_success(self, app):
        client, db = app
        db.add_result(data=[])     
        db.add_result(data=[{}])
        resp = client.post("/auth/register", json={"username": "newuser", "password": "password1"})
        assert resp.status_code == 201
        assert "Account created" in resp.json()["message"]

    def test_register_duplicate_username(self, app):
        client, db = app
        db.add_result(data=[{"id": "existing"}])
        resp = client.post("/auth/register", json={"username": "taken", "password": "password1"})
        assert resp.status_code == 409
        assert "already taken" in resp.json()["detail"]

    def test_register_short_username(self, app):
        client, db = app
        resp = client.post("/auth/register", json={"username": "ab", "password": "password1"})
        assert resp.status_code == 422

    def test_register_short_password(self, app):
        client, db = app
        resp = client.post("/auth/register", json={"username": "validuser", "password": "short"})
        assert resp.status_code == 422

    def test_register_invalid_username_chars(self, app):
        client, db = app
        resp = client.post("/auth/register", json={"username": "bad user!", "password": "password1"})
        assert resp.status_code == 422


class TestLogin:
    def _user(self, password="password1", role="user", is_approved=True):
        return {
            "id": "user-123", "username": "alice",
            "password": hash_password(password),
            "role": role, "is_approved": is_approved,
        }

    def test_login_success(self, app):
        client, db = app
        db.add_result(data=[self._user()])
        db.add_result(data=[])
        resp = client.post("/auth/login", json={"username": "alice", "password": "password1"})
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert body["username"] == "alice"
        assert body["role"] == "user"

    def test_login_wrong_password(self, app):
        client, db = app
        db.add_result(data=[self._user()])
        resp = client.post("/auth/login", json={"username": "alice", "password": "wrongpassword"})
        assert resp.status_code == 401

    def test_login_unknown_user(self, app):
        client, db = app
        db.add_result(data=[])
        resp = client.post("/auth/login", json={"username": "nobody", "password": "password1"})
        assert resp.status_code == 401

    def test_login_unapproved_user(self, app):
        client, db = app
        db.add_result(data=[self._user(is_approved=False)])
        resp = client.post("/auth/login", json={"username": "alice", "password": "password1"})
        assert resp.status_code == 403
        assert "pending" in resp.json()["detail"]

    def test_login_admin_bypasses_approval(self, app):
        client, db = app
        db.add_result(data=[self._user(role="admin", is_approved=False)])
        db.add_result(data=[])
        resp = client.post("/auth/login", json={"username": "alice", "password": "password1"})
        assert resp.status_code == 200