from fastapi import APIRouter

from backend.routes.collections import crud, ingest, items

router = APIRouter(tags=["Collections"])

router.include_router(crud.router)
router.include_router(items.router)
router.include_router(ingest.router)