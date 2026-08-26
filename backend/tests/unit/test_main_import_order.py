import ast
from pathlib import Path

MAIN_PY = Path(__file__).resolve().parent.parent.parent / "main.py"


def _top_level_import_positions(source: str) -> dict[str, int]:
    """
    Maps each top-level `from X import ...` module name to the position
    (index among all top-level statements) at which it appears in the
    file. Only the first match per module name is recorded.
    """
    tree = ast.parse(source)
    positions: dict[str, int] = {}
    for i, node in enumerate(tree.body):
        if isinstance(node, ast.ImportFrom) and node.module:
            positions.setdefault(node.module, i)
    return positions


class TestMainImportOrder:
    """
    Regression guard for the Windows-only crash documented in main.py:
    importing the route modules (which pull in the Gemini SDK's native
    grpc/protobuf deps) before torch/sentence-transformers causes a DLL
    collision (0xC0000005). The reranker (and embeddings) imports must
    stay above the routes import. This test has no runtime/import side
    effects of its own — it only parses main.py's source as text, so it
    doesn't require torch or any other heavy dependency to be installed.
    """

    def test_main_py_exists(self):
        assert MAIN_PY.is_file(), f"expected to find main.py at {MAIN_PY}"

    def test_reranker_imported_before_routes(self):
        source = MAIN_PY.read_text()
        positions = _top_level_import_positions(source)

        assert "services.reranker" in positions, (
            "backend.main no longer imports backend.services.reranker at "
            "the top level — if the reranker warm-up was refactored (e.g. "
            "into a lazy import), this test should be updated or removed "
            "rather than silently skipped."
        )
        assert "routes" in positions, (
            "backend.main no longer imports backend.routes at the top "
            "level — update this test to match the new import structure."
        )

        assert positions["services.reranker"] < positions["routes"], (
            "backend.services.reranker must be imported before backend.routes "
            "in main.py. Importing the routes first pulls in the Gemini SDK's "
            "native deps (grpc/protobuf) ahead of torch, which causes a "
            "Windows DLL collision (0xC0000005). See the comment at the top "
            "of main.py for details."
        )

    def test_embeddings_imported_before_routes(self):
        """
        embeddings.py itself only imports ollama (no torch), so it isn't
        implicated in the DLL collision. It's kept ahead of the routes
        import purely to warm up alongside the reranker in one block —
        this just guards against that block being split apart by accident.
        """
        source = MAIN_PY.read_text()
        positions = _top_level_import_positions(source)

        assert "services.embeddings" in positions
        assert "routes" in positions
        assert positions["services.embeddings"] < positions["routes"]