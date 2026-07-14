_TYPE_COLOR = {
    "documents": "#6C63FF",
    "urls":      "#3498DB",
    "text":      "#2ECC71",
}
_TYPE_ICON = {
    "documents": "📄",
    "urls":      "🔗",
    "text":      "📝",
}
COLLECTION_TYPES = ["documents", "urls", "text"]

_UPLOADABLE_TYPES = {
    "documents": ["pdf"],
    "text": ["txt"],
}

_STATUS_BADGE = {
    "ready":      ("#2ECC71", "Ready"),
    "processing": ("#F5A623", "Processing…"),
    "error":      ("#E74C3C", "Error"),
}

_RETRIEVAL_MODE_OPTIONS = {
    "Semantic": "semantic",
    "Keyword":  "keyword",
    "Hybrid":   "hybrid",
}
_RETRIEVAL_MODE_HELP = (
    "**Semantic** — meaning-based similarity search (the default).\n\n"
    "**Keyword** — BM25 lexical search; best for exact terms, names, or identifiers.\n\n"
    "**Hybrid** — combines both via Reciprocal Rank Fusion."
)

SECTION_HEIGHT = 480
CHAT_SECTION_HEIGHT = 440