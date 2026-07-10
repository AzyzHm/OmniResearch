from typing import Any, Optional, cast

import requests
from google import genai

from backend.config.settings import get_settings
from backend.services.usage_tracker import record_llm_usage

MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"


def _call_gemini(messages: list[dict[str, Any]], temperature: float) -> tuple[str, dict]:
    settings = get_settings()
    client = genai.Client(api_key=settings.gemini_api_key)

    contents: list[dict[str, Any]] = [
        {
            "role": "user" if msg["role"] == "user" else "model",
            "parts": [{"text": msg["content"]}],
        }
        for msg in messages
    ]

    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=cast(Any, contents),
        config=genai.types.GenerateContentConfig(
            temperature=temperature,
        ),
    )

    usage = response.usage_metadata
    usage_dict = {
        "model": settings.gemini_model,
        "prompt_tokens": (getattr(usage, "prompt_token_count", 0) or 0) if usage else 0,
        "completion_tokens": (getattr(usage, "candidates_token_count", 0) or 0) if usage else 0,
        "total_tokens": (getattr(usage, "total_token_count", 0) or 0) if usage else 0,
    }

    text = response.text or "⚠️ The model did not return a response."
    return text, usage_dict


def _call_mistral(messages: list[dict[str, Any]], temperature: float) -> tuple[str, dict]:
    """
    Direct HTTP call via `requests` instead of the `mistralai` SDK, to avoid
    dependency conflicts. Mistral's chat completions API is OpenAI-compatible
    and our messages already use "user"/"assistant" roles, so they pass
    straight through with no role conversion (unlike Gemini's user/model split).
    """
    settings = get_settings()

    response = requests.post(
        MISTRAL_URL,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.mistral_api_key}",
        },
        json={
            "model": settings.mistral_model,
            "messages": messages,
            "temperature": temperature,
            "response_format": {"type": "text"},
        },
        timeout=60,
    )

    if response.status_code != 200:
        raise RuntimeError(f"Mistral API error: {response.status_code} - {response.text}")

    data = response.json()
    content = data["choices"][0]["message"]["content"]

    usage = data.get("usage") or {}
    usage_dict = {
        "model": settings.mistral_model,
        "prompt_tokens": usage.get("prompt_tokens", 0) or 0,
        "completion_tokens": usage.get("completion_tokens", 0) or 0,
        "total_tokens": usage.get("total_tokens", 0) or 0,
    }

    return content or "⚠️ The model did not return a response.", usage_dict


def get_gemini_response(
    messages: list[dict[str, Any]],
    temperature: float = 0.7,
    user_id: Optional[str] = None,
) -> str:
    """
    Call Gemini with a flat message list and return the response text.

    messages format: [{"role": "user"|"assistant", "content": "..."}]

    The Supabase role values ("user" / "assistant") are converted to the
    Gemini SDK role values ("user" / "model") before sending.

    Falls back to Mistral (direct HTTP request, not the mistralai SDK) if
    Gemini fails for any reason — most commonly the free-tier quota limit.
    If Mistral also fails, the error is raised rather than swallowed, so it
    reaches the frontend instead of failing silently.

    Set FORCE_MISTRAL=true in .env to skip Gemini entirely and always use
    Mistral — useful for testing the fallback path without waiting for a
    real quota error or touching your working Gemini key.

    user_id, if provided, is used to attribute token usage to that user for
    the admin usage-monitoring view. Usage recording is best-effort and
    never breaks the response if it fails.
    """
    settings = get_settings()

    if settings.force_mistral:
        print("[LLM] FORCE_MISTRAL is set — skipping Gemini, calling Mistral directly")
        text, usage = _call_mistral(messages, temperature)
        record_llm_usage(user_id, "mistral", **usage)
        return text

    try:
        text, usage = _call_gemini(messages, temperature)
        record_llm_usage(user_id, "gemini", **usage)
        return text
    except Exception as gemini_exc:
        print(f"[LLM] Gemini failed, falling back to Mistral: {gemini_exc}")
        try:
            text, usage = _call_mistral(messages, temperature)
            record_llm_usage(user_id, "mistral", **usage)
            return text
        except Exception as mistral_exc:
            print(f"[LLM] Mistral fallback also failed: {mistral_exc}")
            print(
                f"[LLM] Both providers exhausted — Gemini error: {gemini_exc} | "
                f"Mistral error: {mistral_exc}"
            )
            raise RuntimeError(
                "The base model quota has been reached. Please try again later."
            ) from mistral_exc