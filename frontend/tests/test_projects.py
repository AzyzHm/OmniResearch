import frontend.services.projects as projects


class TestListProjects:
    def test_calls_correct_endpoint(self, mock_call):
        stub = mock_call(projects, return_value=[{"id": "p1", "name": "My Project"}])
        result = projects.list_projects("tok")
        stub.assert_called_once_with("GET", "/projects", token="tok")
        assert result == [{"id": "p1", "name": "My Project"}]

    def test_none_response_falls_back_to_empty_list(self, mock_call):
        mock_call(projects, return_value=None)
        result = projects.list_projects("tok")
        assert result == []


class TestCreateProject:
    def test_calls_correct_endpoint(self, mock_call):
        stub = mock_call(projects, return_value={"id": "p1", "name": "New Project"})
        result = projects.create_project("tok", "New Project")
        stub.assert_called_once_with(
            "POST", "/projects", token="tok", json={"name": "New Project"}
        )
        assert result["name"] == "New Project"


class TestRenameProject:
    def test_calls_correct_endpoint(self, mock_call):
        stub = mock_call(projects, return_value={"id": "p1", "name": "Renamed"})
        result = projects.rename_project("tok", "p1", "Renamed")
        stub.assert_called_once_with(
            "PUT", "/projects/p1", token="tok", json={"name": "Renamed"}
        )
        assert result["name"] == "Renamed"


class TestDeleteProject:
    def test_calls_correct_endpoint(self, mock_call):
        stub = mock_call(projects, return_value=None)
        projects.delete_project("tok", "p1")
        stub.assert_called_once_with("DELETE", "/projects/p1", token="tok")