def make_token(user_id="user-123", username="testuser", role="user") -> str:
    from config.auth import create_access_token

    return create_access_token(user_id=user_id, username=username, role=role)


def make_admin_token(user_id="admin-001", username="admin") -> str:
    return make_token(user_id=user_id, username=username, role="admin")


def make_superadmin_token(user_id="superadmin-001", username="root") -> str:
    return make_token(user_id=user_id, username=username, role="superadmin")
