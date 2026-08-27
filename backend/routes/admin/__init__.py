from fastapi import APIRouter

from backend.routes.admin import logs, quota, stats, usage, users

router = APIRouter(prefix="/admin", tags=["Administration"])

router.include_router(users.router)
router.include_router(quota.router)
router.include_router(logs.router)
router.include_router(stats.router)
router.include_router(usage.router)