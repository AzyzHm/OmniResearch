from typing import Any, cast

from fastapi import APIRouter, Depends

from backend.config.auth import require_admin
from backend.database.db import get_supabase

router = APIRouter()


@router.get(
    "/stats",
    summary="Aggregate admin statistics",
)
async def get_stats(current_admin: dict = Depends(require_admin)):
    db = get_supabase()
    requester_role = current_admin.get("role")
    requester_id = current_admin["sub"]
    scope_roles = ["user", "admin"] if requester_role == "superadmin" else ["user"]

    users_result: Any = db.table("users").select("id, role, is_approved").in_("role", scope_roles).execute()
    scoped_users = [u for u in cast(list[dict[str, Any]], users_result.data) if u["id"] != requester_id]
    scoped_user_ids = [u["id"] for u in scoped_users]

    total_users   = len([u for u in scoped_users if u["role"] == "user"])
    admin_users   = len([u for u in scoped_users if u["role"] == "admin"])
    pending_users = len([u for u in scoped_users if u["role"] == "user" and not u["is_approved"]])

    total_logins = 0
    recent_data: list[dict[str, Any]] = []
    if scoped_user_ids:
        logins_result: Any = (
            db.table("login_logs").select("id", count="exact") # type: ignore
            .in_("user_id", scoped_user_ids).execute()
        )
        total_logins = logins_result.count or 0

        recent: Any = (
            db.table("login_logs")
            .select("username, login_time, ip_address")
            .in_("user_id", scoped_user_ids)
            .order("login_time", desc=True)
            .limit(7)
            .execute()
        )
        recent_data = recent.data or []

    stats: dict[str, Any] = {
        "total_users": total_users,
        "pending_users": pending_users,
        "total_logins": total_logins,
        "recent_logins": recent_data,
    }
    if requester_role == "superadmin":
        stats["admin_users"] = admin_users
    return stats