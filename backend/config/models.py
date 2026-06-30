from typing import Any, cast

from google import genai
from backend.config.settings import get_settings

def get_gemini_response(messages: list[dict], temperature: float = 0.7) -> str:
    """
    Call Gemini with a flat message list and return the response text.
 
    messages format: [{"role": "user"|"assistant", "content": "..."}]
 
    The Supabase role values ("user" / "assistant") are converted to the
    Gemini SDK role values ("user" / "model") before sending.
    """
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