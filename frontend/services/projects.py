from frontend.services.base import _call


def list_projects(token: str) -> list:
    return _call("GET", "/projects", token=token) or []


def create_project(token: str, name: str) -> dict:
    return _call("POST", "/projects", token=token, json={"name": name})


def rename_project(token: str, project_id: str, name: str) -> dict:
    return _call("PUT", f"/projects/{project_id}", token=token, json={"name": name})


def delete_project(token: str, project_id: str) -> None:
    _call("DELETE", f"/projects/{project_id}", token=token)