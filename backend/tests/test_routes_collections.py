from backend.tests.conftest import project_row, collection_row


class TestCollectionRoutes:
    def test_list_collections(self, app, user_headers):
        client, db = app
        db.add_result(data=[project_row()])
        db.add_result(data=[collection_row(), collection_row("col-2", name="B")])
        resp = client.get("/projects/proj-1/collections", headers=user_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_list_collections_project_not_found(self, app, user_headers):
        client, db = app
        db.add_result(data=[])
        resp = client.get("/projects/bad-id/collections", headers=user_headers)
        assert resp.status_code == 404

    def test_list_collections_unauthenticated(self, app):
        client, _ = app
        resp = client.get("/projects/proj-1/collections")
        assert resp.status_code in (401, 403)

    def test_create_collection_documents(self, app, user_headers):
        client, db = app
        db.add_result(data=[project_row()])
        db.add_result(data=[collection_row()])
        resp = client.post(
            "/projects/proj-1/collections",
            json={"name": "My Coll", "type": "documents"},
            headers=user_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "My Coll"

    def test_create_collection_urls(self, app, user_headers):
        client, db = app
        db.add_result(data=[project_row()])
        db.add_result(data=[collection_row(type_="urls")])
        resp = client.post(
            "/projects/proj-1/collections",
            json={"name": "Links", "type": "urls"},
            headers=user_headers,
        )
        assert resp.status_code == 201

    def test_create_collection_invalid_type(self, app, user_headers):
        client, _ = app
        resp = client.post(
            "/projects/proj-1/collections",
            json={"name": "Bad", "type": "video"},
            headers=user_headers,
        )
        assert resp.status_code == 422

    def test_create_collection_empty_name(self, app, user_headers):
        client, _ = app
        resp = client.post(
            "/projects/proj-1/collections",
            json={"name": "  ", "type": "documents"},
            headers=user_headers,
        )
        assert resp.status_code == 422

    def test_delete_collection_success(self, app, user_headers):
        client, db = app
        db.add_result(data=[collection_row()])
        db.add_result(data=[])
        resp = client.delete("/collections/col-1", headers=user_headers)
        assert resp.status_code == 204

    def test_delete_collection_not_found(self, app, user_headers):
        client, db = app
        db.add_result(data=[])
        resp = client.delete("/collections/missing", headers=user_headers)
        assert resp.status_code == 404

    def test_delete_collection_wrong_owner(self, app, user_headers):
        client, db = app
        col = collection_row()
        col["projects"] = {"user_id": "other-user"}
        db.add_result(data=[col])
        resp = client.delete("/collections/col-1", headers=user_headers)
        assert resp.status_code == 404