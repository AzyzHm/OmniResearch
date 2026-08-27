from fastapi import APIRouter

from backend.routes.notes import crud, items

router = APIRouter(tags=["Notes"])

router.include_router(crud.router)
router.include_router(items.router)