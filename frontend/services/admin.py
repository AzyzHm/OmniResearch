from frontend.services.base import _call


def admin_list_users(token: str, pending_only: bool = False) -> dict:
    return _call("GET", "/admin/users", token=token, params={"pending_only": pending_only})


def admin_approve_user(token: str, user_id: str) -> dict:
    return _call("PUT", f"/admin/users/{user_id}/approve", token=token)


def admin_change_role(token: str, user_id: str, new_role: str) -> dict:
    return _call("PUT", f"/admin/users/{user_id}/role", token=token, params={"new_role": new_role})


def admin_delete_user(token: str, user_id: str) -> dict:
    return _call("DELETE", f"/admin/users/{user_id}", token=token)


def admin_get_logs(token: str, limit: int = 100, offset: int = 0, username: str = "") -> dict:
    params: dict = {"limit": limit, "offset": offset}
    if username:
        params["username"] = username
    return _call("GET", "/admin/logs", token=token, params=params)


def admin_get_stats(token: str) -> dict:
    return _call("GET", "/admin/stats", token=token)


def admin_get_llm_usage(token: str) -> dict:
    return _call("GET", "/admin/usage/llm", token=token)


def admin_get_search_usage(token: str) -> dict:
    return _call("GET", "/admin/usage/search", token=token)