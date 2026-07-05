import os
import sys
from datetime import datetime, timezone
from unittest.mock import MagicMock

os.environ["SUPABASE_URL"] = "https://fake.supabase.co"
os.environ["SUPABASE_SERVICE_KEY"] = "fake-service-key"
os.environ["JWT_SECRET"] = "test-secret-key-for-unit-tests-only"
os.environ["GEMINI_API_KEY"] = "fake-gemini-key"
os.environ["GEMINI_MODEL"] = "gemini-2.5-flash"
os.environ["MISTRAL_API_KEY"] = "fake-mistral-key"
os.environ["MISTRAL_MODEL"] = "mistral-small-2506"
os.environ["FORCE_MISTRAL"] = "false"
os.environ["JINA_API_KEY"] = "fake-jina-key"
os.environ["TAVILY_API_KEY"] = "fake-tavily-key"
os.environ["EXA_API_KEY"] = "fake-exa-key"

for _mod in [
    "chromadb", "chromadb.config",
    "google", "google.genai",
    "supabase",
    "ollama",
    "exa_py",
    "tavily",
]:
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


class FakeRAGGraph:
    """
    Stand-in for the compiled LangGraph RAG pipeline. Configure `.answer`
    or `.raise_exc` before making a request to control the outcome of
    POST /chats/{id}/message and /message/stream.
    """
    def __init__(self, answer="Mocked AI reply", raise_exc=None):
        self.answer = answer
        self.raise_exc = raise_exc
        self.last_invoke_state = None

    def invoke(self, state):
        self.last_invoke_state = state
        if self.raise_exc:
            raise self.raise_exc
        return {"answer": self.answer}

    def stream(self, state, stream_mode="updates"):
        self.last_invoke_state = state
        if self.raise_exc:
            raise self.raise_exc
        yield {"router": {"needs_retrieval": False}}
        yield {"generate": {"answer": self.answer}}


class FakeDB:
    def __init__(self):
        self._queue: list[FakeResult] = []
        self._default = FakeResult(data=[], count=0)
        self.rag_graph = FakeRAGGraph()

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
    Also replaces the compiled RAG graph and the Gemini call so chat tests
    never touch a real model or vector store.
    """
    import backend.config.models as models_mod
    import backend.routes.chat as r_chat
    import backend.services.usage_tracker as usage_mod
    from backend.config.settings import get_settings

    fake_db = FakeDB()
    restore = _patch_all_get_supabase(fake_db)

    _orig_gemini_mod = getattr(models_mod, "get_gemini_response", None)
    _gemini_stub = lambda *a, **kw: "Mocked AI reply"
    models_mod.get_gemini_response = _gemini_stub

    _orig_get_rag_graph = getattr(r_chat, "get_rag_graph", None)
    r_chat.get_rag_graph = lambda: fake_db.rag_graph

    _orig_usage_supabase = getattr(usage_mod, "get_supabase", None)
    usage_mod.get_supabase = lambda: fake_db

    get_settings.cache_clear()

    from backend.main import app as _app
    with TestClient(_app, raise_server_exceptions=True) as client:
        yield client, fake_db

    restore()
    if _orig_gemini_mod is not None:
        models_mod.get_gemini_response = _orig_gemini_mod
    if _orig_get_rag_graph is not None:
        r_chat.get_rag_graph = _orig_get_rag_graph
    if _orig_usage_supabase is not None:
        usage_mod.get_supabase = _orig_usage_supabase


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

def message_row(msg_id="msg-1", chat_id="chat-1", role="user", content="Hello"):
    return {"id": msg_id, "chat_id": chat_id, "role": role, "content": content,
            "created_at": NOW}

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
            setattr(m, "get_supabase", orig)

    return restore