import os
import sys
import types
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
    "chromadb",
    "chromadb.config",
    "chromadb.base_types",
    "chromadb.api",
    "chromadb.utils",
    "chromadb.utils.embedding_functions",
    "google",
    "google.genai",
    "supabase",
    "ollama",
    "exa_py",
    "tavily",
    "torch",
    "torch.cuda",
    "torch.backends",
    "torch.backends.mps",
    "sentence_transformers",
]:
    sys.modules.setdefault(_mod, MagicMock())


class MockChromaNotFoundError(Exception):
    """Stand-in for chromadb.errors.NotFoundError while chromadb is mocked."""


_chromadb_errors = types.ModuleType("chromadb.errors")
_chromadb_errors.NotFoundError = MockChromaNotFoundError  # type: ignore[attr-defined]
sys.modules.setdefault("chromadb.errors", _chromadb_errors)
