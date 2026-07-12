import torch
from sentence_transformers import CrossEncoder

from backend.config.settings import get_settings

_model: "CrossEncoder | None" = None


def _select_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def warm_up_reranker() -> None:
    """
    Load the cross-encoder onto GPU (or MPS/CPU) once at backend startup,
    mirroring warm_up_embedding_model() for embeddinggemma — the first real
    chat request shouldn't pay for a cold model load.
    """
    global _model
    settings = get_settings()
    try:
        device = _select_device()
        model = CrossEncoder(settings.reranker_model_name, max_length=512, device=device)
        model.predict([("warmup", "warmup")])
        _model = model
        print(f"✅ Reranker '{settings.reranker_model_name}' is warmed up on {device.upper()}.")
    except Exception as exc:
        print(f"⚠️ Could not warm up reranker '{settings.reranker_model_name}': {exc}")


def _get_model() -> CrossEncoder:
    global _model
    if _model is None:
        warm_up_reranker()
    if _model is None:
        raise RuntimeError("Reranker model failed to load.")
    return _model


def rerank(query: str, chunks: list[dict], top_k: int = 5) -> list[dict]:
    """
    Re-score a candidate pool of chunks against the query with the
    cross-encoder and return the top_k highest-scoring ones. Each returned
    chunk gets a 'rerank_score' field attached (higher = more relevant).
    """
    if not chunks:
        return []

    model = _get_model()
    pairs = [(query, chunk["content"]) for chunk in chunks]
    scores = model.predict(pairs)

    scored = [
        {**chunk, "rerank_score": float(score)}
        for chunk, score in zip(chunks, scores)
    ]
    scored.sort(key=lambda c: c["rerank_score"], reverse=True)
    return scored[:top_k]