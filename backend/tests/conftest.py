import pytest
from fastapi.testclient import TestClient

from tests.setup.fakes import FakeDB
from tests.setup.patches import patch_all_get_supabase
from tests.setup.tokens import make_admin_token, make_superadmin_token, make_token


@pytest.fixture()
def app():
    """
    Yields (TestClient, FakeDB).

    Replaces get_supabase in every module that imported it directly, and
    replaces the compiled RAG graph and the Gemini call so chat tests
    never touch a real model or vector store.
    """
    import config.models as models_mod
    import routes.chat.send as r_chat_send
    import services.quota as quota_mod
    import services.usage_tracker as usage_mod
    from config.settings import get_settings

    fake_db = FakeDB()
    restore = patch_all_get_supabase(fake_db)

    _orig_gemini_mod = getattr(models_mod, "get_gemini_response", None)
    models_mod.get_gemini_response = lambda *a, **kw: "Mocked AI reply"

    _orig_get_rag_graph = getattr(r_chat_send, "get_rag_graph", None)
    r_chat_send.get_rag_graph = lambda: fake_db.rag_graph

    _orig_usage_supabase = getattr(usage_mod, "get_supabase", None)
    usage_mod.get_supabase = lambda: fake_db

    _orig_quota_supabase = getattr(quota_mod, "get_supabase", None)
    quota_mod.get_supabase = lambda: fake_db

    get_settings.cache_clear()

    from main import app as _app
    with TestClient(_app, raise_server_exceptions=True) as client:
        yield client, fake_db

    restore()
    if _orig_gemini_mod is not None:
        models_mod.get_gemini_response = _orig_gemini_mod
    if _orig_get_rag_graph is not None:
        r_chat_send.get_rag_graph = _orig_get_rag_graph
    if _orig_usage_supabase is not None:
        usage_mod.get_supabase = _orig_usage_supabase
    if _orig_quota_supabase is not None:
        quota_mod.get_supabase = _orig_quota_supabase


@pytest.fixture()
def user_headers():
    return {"Authorization": f"Bearer {make_token()}"}


@pytest.fixture()
def admin_headers():
    return {"Authorization": f"Bearer {make_admin_token()}"}


@pytest.fixture()
def superadmin_headers():
    return {"Authorization": f"Bearer {make_superadmin_token()}"}