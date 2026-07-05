from frontend.services.base import _call


def search_web(
    token: str, engine: str, query: str, num_results: int = 10, search_depth: str = "basic"
) -> list:
    result = _call(
        "POST",
        "/search/web",
        token=token,
        json={
            "engine": engine,
            "query": query,
            "num_results": num_results,
            "search_depth": search_depth,
        },
    )
    return (result or {}).get("results", [])


def add_search_result_items(token: str, collection_id: str, items: list) -> dict:
    """items: list of {"url": ..., "title": ..., "content": ...} dicts."""
    return _call(
        "POST",
        f"/collections/{collection_id}/items/from-search",
        token=token,
        json={"items": items},
    )