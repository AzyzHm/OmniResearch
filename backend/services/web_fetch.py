import requests

from backend.config.settings import get_settings


def fetch_url_markdown(url: str) -> str:
    """Fetch a URL's readable content as markdown via the Jina Reader API."""
    settings = get_settings()
    response = requests.get(
        f"https://r.jina.ai/{url}",
        headers={"Authorization": f"Bearer {settings.jina_api_key}"},
        timeout=30,
    )
    if response.status_code != 200:
        raise ValueError(f"Jina fetch failed ({response.status_code}): {response.text[:200]}")
    return response.text