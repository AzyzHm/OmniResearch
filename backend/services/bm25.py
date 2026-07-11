import json

from chromadb.base_types import SparseVector
from chromadb.utils.embedding_functions import ChromaBm25EmbeddingFunction

_bm25_ef = ChromaBm25EmbeddingFunction(k=1.2, b=0.75, avg_doc_length=256.0, token_max_length=40)


def bm25_sparse_vector(text: str) -> SparseVector:
    """Compute a single BM25 sparse vector for one piece of text."""
    return _bm25_ef([text])[0]


def bm25_sparse_vectors(texts: list[str]) -> list[SparseVector]:
    """Compute BM25 sparse vectors for a batch of texts in one call (used at
    ingestion time, one call per file/URL rather than one per chunk)."""
    if not texts:
        return []
    return _bm25_ef(texts)


def sparse_vector_to_metadata(sv: SparseVector) -> dict[str, str]:
    """
    Serialize a SparseVector into Chroma-metadata-safe fields. Chroma
    metadata values must be str/int/float/bool — not lists — so the
    indices/values arrays are stored as JSON strings.
    """
    return {
        "bm25_indices": json.dumps(list(sv.indices)),
        "bm25_values": json.dumps(list(sv.values)),
    }


def sparse_vector_from_metadata(meta: dict) -> tuple[list[int], list[float]]:
    """Reverse of sparse_vector_to_metadata. Returns ([], []) for chunks
    added before this feature existed (no bm25_* fields yet) — they simply
    won't participate in keyword/hybrid scoring until reprocessed."""
    try:
        indices = json.loads(meta.get("bm25_indices") or "[]")
        values = json.loads(meta.get("bm25_values") or "[]")
        return indices, values
    except (TypeError, ValueError):
        return [], []


def sparse_dot(
    q_indices: list[int], q_values: list[float], d_indices: list[int], d_values: list[float],
) -> float:
    """
    Sparse dot product between a query BM25 vector and a document BM25
    vector — this is the actual scoring step Chroma's managed Knn()/Rrf()
    would do server-side on Chroma Cloud; done manually here for local use.
    """
    if not q_indices or not d_indices:
        return 0.0
    q_map = dict(zip(q_indices, q_values))
    return sum(q_map[idx] * val for idx, val in zip(d_indices, d_values) if idx in q_map)