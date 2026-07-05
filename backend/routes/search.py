from fastapi import APIRouter, Depends, HTTPException, status

from backend.config.auth import get_current_user
from backend.models.search import WebSearchRequest, WebSearchResponse
from backend.services.usage_tracker import record_search_usage
from backend.services.web_search import search_web

router = APIRouter(tags=["Search"])


@router.post("/search/web", response_model=WebSearchResponse)
async def search_web_route(
    body: WebSearchRequest,
    current_user: dict = Depends(get_current_user),
):
    try:
        results = search_web(
            engine=body.engine,
            query=body.query,
            num_results=body.num_results,
            search_depth=body.search_depth or "basic",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Search error: {exc}",
        )

    record_search_usage(
        user_id=current_user["sub"],
        engine=body.engine,
        num_results=body.num_results,
        search_depth=body.search_depth,
    )

    return {"results": results}