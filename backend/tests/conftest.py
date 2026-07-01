import os
import sys
from datetime import datetime, timezone
from unittest.mock import MagicMock

os.environ["SUPABASE_URL"] = "https://fake.supabase.co"
os.environ["SUPABASE_SERVICE_KEY"] = "fake-service-key"
os.environ["JWT_SECRET"] = "test-secret-key-for-unit-tests-only"
os.environ["GEMINI_API_KEY"] = "fake-gemini-key"
os.environ["GEMINI_MODEL"] = "gemini-2.5-flash"

for _mod in ["chromadb", "chromadb.config", "google", "google.genai", "supabase"]:
    sys.modules.setdefault(_mod, MagicMock())

import pytest
from fastapi.testclient import TestClient


def make_token(user_id="user-123", username="testuser", role="user") -> str:
    from backend.config.auth import create_access_token
    return create_access_token(user_id=user_id, username=username, role=role)

def make_admin_token(user_id="admin-001", username="admin") -> str:
    return make_token(user_id=user_id, username=username, role="admin")

class FakeResult:
    def __init__(self, data=None, count=None):
        self.data = [] if data is None else data
        self.count = count


class FakeQuery:
    """Fluent query builder whose .execute() pops the next queued result."""
    def __init__(self, result: FakeResult):
        self._result = result

    def __getattr__(self, name):
        def _method(*args, **kwargs):
            return self
        return _method

    def execute(self) -> FakeResult:
        return self._result


class FakeDB:
    def __init__(self):
        self._queue: list[FakeResult] = []
        self._default = FakeResult(data=[], count=0)

    def add_result(self, data=None, count=None) -> "FakeDB":
        self._queue.append(FakeResult(data=data, count=count))
        return self

    def table(self, _name: str) -> FakeQuery:
        result = self._queue.pop(0) if self._queue else self._default
        return FakeQuery(result)


@pytest.fixture()
def app():
    """
    Yields (TestClient, FakeDB).

    Replaces get_supabase in every module that imported it directly
    (since `from x import f` binds f locally, patching the source module
    is not enough — each consumer module's reference must be replaced).
    """
    import backend.config.models as models_mod
    import backend.routes.chat as r_chat
    from backend.config.settings import get_settings

    fake_db = FakeDB()
    restore = _patch_all_get_supabase(fake_db)

    _orig_gemini_mod  = getattr(models_mod, "get_gemini_response", None)
    _orig_gemini_chat = getattr(r_chat, "get_gemini_response", None)
    _gemini_stub = lambda *a, **kw: "Mocked AI reply"
    models_mod.get_gemini_response = _gemini_stub
    r_chat.get_gemini_response = _gemini_stub

    get_settings.cache_clear()

    from backend.main import app as _app
    with TestClient(_app, raise_server_exceptions=True) as client:
        yield client, fake_db

    restore()
    if _orig_gemini_mod is not None:
        models_mod.get_gemini_response = _orig_gemini_mod
    if _orig_gemini_chat is not None:
        r_chat.get_gemini_response = _orig_gemini_chat


@pytest.fixture()
def user_headers():
    return {"Authorization": f"Bearer {make_token()}"}

@pytest.fixture()
def admin_headers():
    return {"Authorization": f"Bearer {make_admin_token()}"}


NOW = datetime.now(timezone.utc).isoformat()

def project_row(project_id="proj-1", user_id="user-123", name="My Project"):
    return {"id": project_id, "user_id": user_id, "name": name,
            "created_at": NOW, "updated_at": NOW}

def collection_row(collection_id="col-1", project_id="proj-1",
                   name="My Coll", type_="documents"):
    return {"id": collection_id, "project_id": project_id, "name": name,
            "type": type_, "created_at": NOW,
            "projects": {"user_id": "user-123"}}

def chat_row(chat_id="chat-1", project_id="proj-1", name="My Chat"):
    return {"id": chat_id, "project_id": project_id, "name": name,
            "created_at": NOW, "projects": {"user_id": "user-123"}}

def user_row(user_id="user-abc", username="alice", role="user", is_approved=True):
    return {"id": user_id, "username": username, "role": role,
            "is_approved": is_approved, "created_at": NOW}


def _patch_all_get_supabase(fake_db):
    """
    Replace `get_supabase` in every route module that imported it directly.
    Returns a restore function.
    """
    import backend.routes.auth as r_auth
    import backend.routes.admin as r_admin
    import backend.routes.projects as r_projects
    import backend.routes.chat as r_chat
    import backend.routes.collections as r_collections
    import backend.database.db as db_mod

    modules = [r_auth, r_admin, r_projects, r_chat, r_collections, db_mod]
    originals = {m: m.get_supabase for m in modules}

    stub = lambda: fake_db
    for m in modules:
        setattr(m, "get_supabase", stub)

    def restore():
        for m, orig in originals.items():
            setattr(m, "get_supabase", stub)

    return restore