import frontend.services.auth as auth


class TestRegister:
    def test_calls_correct_endpoint(self, mock_call):
        stub = mock_call(auth, return_value={"message": "Account created."})
        result = auth.register("alice", "password123")
        stub.assert_called_once_with(
            "POST", "/auth/register",
            json={"username": "alice", "password": "password123"},
        )
        assert result == {"message": "Account created."}

    def test_propagates_call_errors(self, mock_call):
        mock_call(auth, side_effect=RuntimeError("Username already taken"))
        try:
            auth.register("alice", "password123")
            assert False, "expected RuntimeError"
        except RuntimeError as exc:
            assert "Username already taken" in str(exc)


class TestLogin:
    def test_calls_correct_endpoint(self, mock_call):
        stub = mock_call(auth, return_value={"access_token": "tok", "role": "user"})
        result = auth.login("alice", "password123")
        stub.assert_called_once_with(
            "POST", "/auth/login",
            json={"username": "alice", "password": "password123"},
        )
        assert result["access_token"] == "tok"

    def test_propagates_call_errors(self, mock_call):
        mock_call(auth, side_effect=RuntimeError("Invalid username or password"))
        try:
            auth.login("alice", "wrong")
            assert False, "expected RuntimeError"
        except RuntimeError as exc:
            assert "Invalid username or password" in str(exc)