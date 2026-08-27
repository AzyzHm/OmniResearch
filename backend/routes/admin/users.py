from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.config.auth import require_admin, require_superadmin
from backend.database.db import get_supabase
from backend.models import MessageResponse, UserListResponse, UserOut

router = APIRouter()


@router.get(
    "/users",
    response_model=UserListResponse,
    summary="List all registered users",
)
async def list_users(
    current_admin: dict = Depends(require_admin),
    pending_only: bool = Query(False, description="Return only unapproved accounts"),
):
    db = get_supabase()
    query = db.table("users").select("id, username, role, is_approved, created_at, daily_token_limit").order("created_at", desc=True)
    if pending_only:
        query = query.eq("is_approved", False)
    result = query.execute()
    all_users = cast(list[dict[str, Any]], result.data)

    requester_role = current_admin.get("role")
    requester_id = current_admin["sub"]

    if requester_role == "superadmin":
        visible = [u for u in all_users if u["id"] != requester_id]
    else:
        visible = [u for u in all_users if u["role"] == "user"]

    users = [UserOut(**u) for u in visible]
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
    summary="Change a user's role (admin ↔ user) — super admin only",
)
async def change_role(
    user_id: str,
    new_role: str = Query(..., pattern="^(admin|user)$"),
    current_admin: dict = Depends(require_superadmin),
):
    db = get_supabase()

    if current_admin["sub"] == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot change your own role.",
        )

    result: Any = db.table("users").select("id, username, role").eq("id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    target = result.data[0]
    if target["role"] == "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The super admin's role cannot be changed.",
        )

    db.table("users").update({"role": new_role}).eq("id", user_id).execute()
    return MessageResponse(message=f"Role of '{target['username']}' updated to '{new_role}'.")


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

    result : Any = db.table("users").select("id, username, role").eq("id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    target = result.data[0]
    if target["role"] == "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The super admin account cannot be deleted.",
        )
    if current_admin.get("role") == "admin" and target["role"] != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins can only delete regular user accounts.",
        )

    db.table("users").delete().eq("id", user_id).execute()
    return MessageResponse(message=f"User '{target['username']}' has been deleted.")