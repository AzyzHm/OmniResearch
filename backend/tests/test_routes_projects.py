from tests.conftest import project_row


class TestProjectRoutes:
    def test_list_projects_returns_rows(self, app, user_headers):
        client, db = app
        db.add_result(data=[project_row("p1"), project_row("p2", name="Second")])
        resp = client.get("/projects", headers=user_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_list_projects_empty(self, app, user_headers):
        client, db = app
        db.add_result(data=[])
        resp = client.get("/projects", headers=user_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_projects_unauthenticated(self, app):
        client, _ = app
        resp = client.get("/projects")
        assert resp.status_code in (401, 403)

    def test_create_project_success(self, app, user_headers):
        client, db = app
        db.add_result(data=[])  # existing-names lookup
        db.add_result(data=[project_row(name="New Project")])
        resp = client.post("/projects", json={"name": "New Project"}, headers=user_headers)
        assert resp.status_code == 201
        assert resp.json()["name"] == "New Project"

    def test_create_project_duplicate_name_gets_numbered(self, app, user_headers):
        client, db = app
        db.add_result(data=[{"id": "proj-1", "name": "Research"}])  # existing-names lookup
        db.add_result(data=[project_row(name="Research (2)")])
        resp = client.post("/projects", json={"name": "Research"}, headers=user_headers)
        assert resp.status_code == 201
        assert resp.json()["name"] == "Research (2)"

    def test_create_project_duplicate_name_case_insensitive(self, app, user_headers):
        client, db = app
        db.add_result(data=[{"id": "proj-1", "name": "Research"}])  # existing-names lookup
        db.add_result(data=[project_row(name="research (2)")])
        resp = client.post("/projects", json={"name": "research"}, headers=user_headers)
        assert resp.status_code == 201
        assert resp.json()["name"] == "research (2)"

    def test_create_project_empty_name(self, app, user_headers):
        client, _ = app
        resp = client.post("/projects", json={"name": "  "}, headers=user_headers)
        assert resp.status_code == 422

    def test_create_project_name_too_long(self, app, user_headers):
        client, _ = app
        resp = client.post("/projects", json={"name": "x" * 101}, headers=user_headers)
        assert resp.status_code == 422

    def test_rename_project_success(self, app, user_headers):
        client, db = app
        db.add_result(data=[project_row()])
        db.add_result(data=[])  # existing-names lookup (excluding self)
        db.add_result(data=[project_row(name="Renamed")])
        resp = client.put("/projects/proj-1", json={"name": "Renamed"}, headers=user_headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Renamed"

    def test_rename_project_duplicate_name_gets_numbered(self, app, user_headers):
        client, db = app
        db.add_result(data=[project_row()])
        db.add_result(data=[{"id": "proj-2", "name": "Other"}])  # existing-names lookup
        db.add_result(data=[project_row(name="Other (2)")])
        resp = client.put("/projects/proj-1", json={"name": "Other"}, headers=user_headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Other (2)"

    def test_rename_project_not_found(self, app, user_headers):
        client, db = app
        db.add_result(data=[])
        resp = client.put("/projects/unknown", json={"name": "X"}, headers=user_headers)
        assert resp.status_code == 404

    def test_delete_project_success(self, app, user_headers):
        client, db = app
        db.add_result(data=[project_row()])
        db.add_result(data=[])
        resp = client.delete("/projects/proj-1", headers=user_headers)
        assert resp.status_code == 204

    def test_delete_project_not_found(self, app, user_headers):
        client, db = app
        db.add_result(data=[])
        resp = client.delete("/projects/missing", headers=user_headers)
        assert resp.status_code == 404

    def test_delete_project_unauthenticated(self, app):
        client, _ = app
        resp = client.delete("/projects/proj-1")
        assert resp.status_code in (401, 403)