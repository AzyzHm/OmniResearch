from frontend.services.base import _call


def register(username: str, password: str) -> dict:
    return _call("POST", "/auth/register", json={"username": username, "password": password})


def login(username: str, password: str) -> dict:
    return _call("POST", "/auth/login", json={"username": username, "password": password})