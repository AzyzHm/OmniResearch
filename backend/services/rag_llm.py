from typing import Any, Optional, cast

from backend.config.models import get_gemini_response
from backend.config.prompts import (
    GENERATION_PROMPT,
    REFINE_QUERY_PROMPT,
    ROUTER_PROMPT,
    VALIDATION_PROMPT,
)


def _format_history(history: list[dict[str, Any]]) -> str:
    if not history:
        return "(no prior conversation)"
    lines = []
    for msg in history:
        speaker = "User" if msg["role"] == "user" else "Assistant"
        lines.append(f"{speaker}: {msg['content']}")
    return "\n".join(lines)


def _format_context(chunks: list[dict[str, Any]]) -> str:
    if not chunks:
        return "(no context retrieved)"
    parts = []
    for i, chunk in enumerate(chunks, start=1):
        source = chunk.get("source_name", "unknown source")
        parts.append(f"[{i}] (Source: {source})\n{chunk['content']}")
    return "\n\n".join(parts)


def _ask(prompt: str, temperature: float = 0.0, user_id: Optional[str] = None) -> str:
    """One-shot LLM call for meta-tasks (routing/refining/validating) — no chat history threading."""
    response = get_gemini_response(
        [{"role": "user", "content": prompt}], temperature=temperature, user_id=user_id
    )
    return response.strip()


def decide_retrieval(history: list[dict[str, Any]], query: str, user_id: Optional[str] = None) -> bool:
    prompt = ROUTER_PROMPT.format(history_text=_format_history(history), query=query)
    answer = _ask(prompt, user_id=user_id).upper()
    return answer.startswith("RETRIEVE")


def refine_query(history: list[dict[str, Any]], query: str, user_id: Optional[str] = None) -> str:
    prompt = REFINE_QUERY_PROMPT.format(history_text=_format_history(history), query=query)
    refined = _ask(prompt, temperature=0.2, user_id=user_id)
    return refined or query


def validate_context(
    query: str, context_chunks: list[dict[str, Any]], user_id: Optional[str] = None
) -> bool:
    prompt = VALIDATION_PROMPT.format(query=query, context_text=_format_context(context_chunks))
    answer = _ask(prompt, user_id=user_id).upper()
    return answer.startswith("SUFFICIENT")


def generate_answer(
    history: list[dict[str, Any]],
    query: str,
    context_chunks: list[dict[str, Any]],
    user_id: Optional[str] = None,
) -> str:
    """
    Final answer generation. The retrieved context + question are folded into
    one final "user" turn appended after the real chat history, so role
    alternation (user/model) stays valid for the Gemini SDK.
    """
    context_text = (
        _format_context(context_chunks)
        if context_chunks
        else "(no additional context — answer from the conversation and general knowledge)"
    )
    prompt = GENERATION_PROMPT.format(context_text=context_text, query=query)
    messages = list(history) + [{"role": "user", "content": prompt}]
    return get_gemini_response(cast(list[dict[str, Any]], messages), temperature=0.7, user_id=user_id)