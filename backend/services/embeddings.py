import logging
from typing import Any, cast

import ollama

from backend.config.settings import get_settings

logger = logging.getLogger(__name__)


def warm_up_embedding_model() -> None:
    """
    Load embeddinggemma into VRAM once, at backend startup, so the first real
    embedding request isn't slowed down by a cold model load.
    """
    settings = get_settings()
    try:
        ollama.embed(model=settings.embedding_model, input="warmup")
        logger.info("Embedding model '%s' is warmed up.", settings.embedding_model)
    except Exception as exc:
        logger.warning("Could not warm up embedding model '%s': %s", settings.embedding_model, exc)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of text chunks via the local Ollama embeddinggemma model."""
    if not texts:
        return []

    settings = get_settings()
    response = ollama.embed(model=settings.embedding_model, input=texts)

    if isinstance(response, dict):
        embeddings = response["embeddings"]
    else:
        embeddings = cast(Any, response).embeddings

    return cast(list[list[float]], embeddings)