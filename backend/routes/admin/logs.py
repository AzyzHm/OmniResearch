from typing import Any, cast

from fastapi import APIRouter, Depends, Query

from backend.config.auth import require_admin
from backend.database.db import get_supabase
from backend.models import LoginLogListResponse, LoginLogOut

router = APIRouter()


@router.get(
    "/logs",
    response_model=LoginLogListResponse,
    summary="Retrieve login activity logs",
)
async def get_logs(
    current_admin: dict = Depends(require_admin),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    username: str = Query(None, description="Filter by username"),
):
    db = get_supabase()
    requester_role = current_admin.get("role")
    requester_id = current_admin["sub"]

    scope_roles = ["user", "admin"] if requester_role == "superadmin" else ["user"]
    users_result: Any = db.table("users").select("id").in_("role", scope_roles).execute()
    scoped_ids = [u["id"] for u in cast(list[dict[str, Any]], users_result.data) if u["id"] != requester_id]

    if not scoped_ids:
        return LoginLogListResponse(logs=[], total=0)

    query = (
        db.table("login_logs")
        .select("id, user_id, username, login_time, ip_address")
        .in_("user_id", scoped_ids)
        .order("login_time", desc=True)
        .range(offset, offset + limit - 1)
    )
    if username:
        query = query.ilike("username", f"%{username}%")

    result = query.execute()
    logs  = [LoginLogOut(**log) for log in cast(list[Any], result.data)]

    count_query = db.table("login_logs").select("id", count="exact").in_("user_id", scoped_ids) # type: ignore
    if username:
        count_query = count_query.ilike("username", f"%{username}%")
    count_result = count_query.execute()
    total = count_result.count or len(logs)

    return LoginLogListResponse(logs=logs, total=total)