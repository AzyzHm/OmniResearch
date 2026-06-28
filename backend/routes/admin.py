from typing import Any, cast
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.config.auth import require_admin
from backend.database.db import get_supabase
from backend.models import (LoginLogListResponse, LoginLogOut, MessageResponse, UserListResponse,UserOut,)

router = APIRouter(prefix="/admin", tags=["Administration"])

@router.get(
    "/users",
    response_model=UserListResponse,
    summary="List all registered users",
)
async def list_users(
    _: dict = Depends(require_admin),
    pending_only: bool = Query(False, description="Return only unapproved accounts"),
):
    db = get_supabase()
    query = db.table("users").select("id, username, role, is_approved, created_at").order("created_at", desc=True)
    if pending_only:
        query = query.eq("is_approved", False)
    result = query.execute()
    users = [UserOut(**u) for u in cast(list[Any], result.data)]
    return UserListResponse(users=users, total=len(users))


@router.put(
    "/users/{user_id}/approve",
    response_model=MessageResponse,
    summary="Approve a pending user account",
)
async def approve_user(user_id: str, _: dict = Depends(require_admin)):
    db = get_supabase()

    result = db.table("users").select("id, username, is_approved").eq("id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    user : Any = result.data[0]
    if user["is_approved"]:
        return MessageResponse(message=f"User '{user['username']}' is already approved.")

    db.table("users").update({"is_approved": True}).eq("id", user_id).execute()
    return MessageResponse(message=f"User '{user['username']}' has been approved successfully.")


@router.put(
    "/users/{user_id}/role",
    response_model=MessageResponse,
    summary="Change a user's role (admin ↔ user)",
)
async def change_role(
    user_id: str,
    new_role: str = Query(..., pattern="^(admin|user)$"),
    current_admin: dict = Depends(require_admin),
):
    db = get_supabase()

    if current_admin["sub"] == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot change your own role.",
        )

    result : Any = db.table("users").select("id, username").eq("id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    username = result.data[0]["username"]
    db.table("users").update({"role": new_role}).eq("id", user_id).execute()
    return MessageResponse(message=f"Role of '{username}' updated to '{new_role}'.")


@router.delete(
    "/users/{user_id}",
    response_model=MessageResponse,
    summary="Permanently delete a user account",
)
async def delete_user(user_id: str, current_admin: dict = Depends(require_admin)):
    db = get_supabase()

    if current_admin["sub"] == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account.",
        )

    result : Any = db.table("users").select("id, username").eq("id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    username = result.data[0]["username"]
    db.table("users").delete().eq("id", user_id).execute()
    return MessageResponse(message=f"User '{username}' has been deleted.")

@router.get(
    "/logs",
    response_model=LoginLogListResponse,
    summary="Retrieve login activity logs",
)
async def get_logs(
    _: dict = Depends(require_admin),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    username: str = Query(None, description="Filter by username"),
):
    db = get_supabase()
    query = (
        db.table("login_logs")
        .select("id, user_id, username, login_time, ip_address")
        .order("login_time", desc=True)
        .range(offset, offset + limit - 1)
    )
    if username:
        query = query.ilike("username", f"%{username}%")

    result = query.execute()
    logs  = [LoginLogOut(**log) for log in cast(list[Any], result.data)]

    count_query = db.table("login_logs").select("id", count="exact") # type: ignore
    if username:
        count_query = count_query.ilike("username", f"%{username}%")
    count_result = count_query.execute()
    total = count_result.count or len(logs)

    return LoginLogListResponse(logs=logs, total=total)


@router.get(
    "/stats",
    summary="Aggregate admin statistics",
)
async def get_stats(_: dict = Depends(require_admin)):
    db = get_supabase()

    total_users   = db.table("users").select("id", count="exact").execute().count or 0 # type: ignore
    pending_users = db.table("users").select("id", count="exact").eq("is_approved", False).execute().count or 0 # type: ignore
    admin_users   = db.table("users").select("id", count="exact").eq("role", "admin").execute().count or 0 # type: ignore
    total_logins  = db.table("login_logs").select("id", count="exact").execute().count or 0 # type: ignore
 
    recent = (
        db.table("login_logs")
        .select("username, login_time, ip_address")
        .order("login_time", desc=True)
        .limit(7)
        .execute()
    )

    return {
        "total_users": total_users,
        "pending_users": pending_users,
        "admin_users": admin_users,
        "approved_users": total_users - pending_users - admin_users,
        "total_logins": total_logins,
        "recent_logins": recent.data,
    }