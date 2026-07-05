import frontend.services.admin as admin


class TestAdminListUsers:
    def test_default_params(self, mock_call):
        stub = mock_call(admin, return_value={"users": [], "total": 0})
        admin.admin_list_users("tok")
        stub.assert_called_once_with(
            "GET", "/admin/users", token="tok", params={"pending_only": False}
        )

    def test_pending_only_true(self, mock_call):
        stub = mock_call(admin, return_value={"users": [], "total": 0})
        admin.admin_list_users("tok", pending_only=True)
        stub.assert_called_once_with(
            "GET", "/admin/users", token="tok", params={"pending_only": True}
        )


class TestAdminApproveUser:
    def test_calls_correct_endpoint(self, mock_call):
        stub = mock_call(admin, return_value={"message": "approved"})
        admin.admin_approve_user("tok", "user-1")
        stub.assert_called_once_with("PUT", "/admin/users/user-1/approve", token="tok")


class TestAdminChangeRole:
    def test_calls_correct_endpoint(self, mock_call):
        stub = mock_call(admin, return_value={"message": "role changed"})
        admin.admin_change_role("tok", "user-1", "admin")
        stub.assert_called_once_with(
            "PUT", "/admin/users/user-1/role",
            token="tok", params={"new_role": "admin"},
        )


class TestAdminDeleteUser:
    def test_calls_correct_endpoint(self, mock_call):
        stub = mock_call(admin, return_value={"message": "deleted"})
        admin.admin_delete_user("tok", "user-1")
        stub.assert_called_once_with("DELETE", "/admin/users/user-1", token="tok")


class TestAdminGetLogs:
    def test_default_params(self, mock_call):
        stub = mock_call(admin, return_value={"logs": [], "total": 0})
        admin.admin_get_logs("tok")
        stub.assert_called_once_with(
            "GET", "/admin/logs", token="tok", params={"limit": 100, "offset": 0}
        )

    def test_custom_pagination(self, mock_call):
        stub = mock_call(admin, return_value={"logs": [], "total": 0})
        admin.admin_get_logs("tok", limit=50, offset=10)
        stub.assert_called_once_with(
            "GET", "/admin/logs", token="tok", params={"limit": 50, "offset": 10}
        )

    def test_username_filter_included_when_provided(self, mock_call):
        stub = mock_call(admin, return_value={"logs": [], "total": 0})
        admin.admin_get_logs("tok", username="alice")
        stub.assert_called_once_with(
            "GET", "/admin/logs", token="tok",
            params={"limit": 100, "offset": 0, "username": "alice"},
        )

    def test_username_filter_omitted_when_empty(self, mock_call):
        stub = mock_call(admin, return_value={"logs": [], "total": 0})
        admin.admin_get_logs("tok", username="")
        _, kwargs = stub.call_args
        assert "username" not in kwargs["params"]


class TestAdminGetStats:
    def test_calls_correct_endpoint(self, mock_call):
        stub = mock_call(admin, return_value={"total_users": 5})
        admin.admin_get_stats("tok")
        stub.assert_called_once_with("GET", "/admin/stats", token="tok")


class TestAdminGetLLMUsage:
    def test_calls_correct_endpoint(self, mock_call):
        stub = mock_call(admin, return_value={"users": []})
        admin.admin_get_llm_usage("tok")
        stub.assert_called_once_with("GET", "/admin/usage/llm", token="tok")


class TestAdminGetSearchUsage:
    def test_calls_correct_endpoint(self, mock_call):
        stub = mock_call(admin, return_value={"users": []})
        admin.admin_get_search_usage("tok")
        stub.assert_called_once_with("GET", "/admin/usage/search", token="tok")