from typing import Any

from exa_py import Exa
from tavily import TavilyClient

from backend.config.settings import get_settings


def search_tavily(query: str, num_results: int, search_depth: str) -> list[dict]:
    settings = get_settings()
    client = TavilyClient(api_key=settings.tavily_api_key)
    response: Any = client.search(
        query=query,
        search_depth=search_depth, #type: ignore
        max_results=num_results,
    )
    return [
        {
            "url": r.get("url", ""),
            "title": r.get("title", ""),
            "content": (r.get("content") or "").strip(),
        }
        for r in response.get("results", [])
    ]


def search_exa(query: str, num_results: int) -> list[dict]:
    settings = get_settings()
    client = Exa(api_key=settings.exa_api_key)
    response: Any = client.search(
        query,
        num_results=num_results,
        type="auto",
        contents={"highlights": True},
    )
    results = []
    for r in getattr(response, "results", None) or []:
        highlights = getattr(r, "highlights", None) or []
        content = "\n\n".join(h for h in highlights if h).strip()
        results.append({
            "url": getattr(r, "url", "") or "",
            "title": getattr(r, "title", "") or "",
            "content": content,
        })
    return results


def search_web(engine: str, query: str, num_results: int, search_depth: str = "basic") -> list[dict]:
    if engine == "tavily":
        return search_tavily(query, num_results, search_depth)
    if engine == "exa":
        return search_exa(query, num_results)
    raise ValueError(f"Unknown search engine: {engine}")