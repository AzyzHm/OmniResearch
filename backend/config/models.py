from typing import Any, cast

import requests
from google import genai

from backend.config.settings import get_settings

MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"


def _call_gemini(messages: list[dict[str, Any]], temperature: float) -> str:
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
    return response.text or "⚠️ The model did not return a response."


def _call_mistral(messages: list[dict[str, Any]], temperature: float) -> str:
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
    return content or "⚠️ The model did not return a response."


def get_gemini_response(messages: list[dict[str, Any]], temperature: float = 0.7) -> str:
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
    """
    settings = get_settings()

    if settings.force_mistral:
        print("[LLM] FORCE_MISTRAL is set — skipping Gemini, calling Mistral directly")
        return _call_mistral(messages, temperature)

    try:
        return _call_gemini(messages, temperature)
    except Exception as gemini_exc:
        print(f"[LLM] Gemini failed, falling back to Mistral: {gemini_exc}")
        try:
            return _call_mistral(messages, temperature)
        except Exception as mistral_exc:
            print(f"[LLM] Mistral fallback also failed: {mistral_exc}")
            raise RuntimeError(
                f"Both Gemini and Mistral failed. "
                f"Gemini error: {gemini_exc}. Mistral error: {mistral_exc}"
            ) from mistral_exc