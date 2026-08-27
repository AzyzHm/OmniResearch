from fastapi import APIRouter

from backend.routes.chat import crud, messages, send

router = APIRouter(tags=["Chats"])

router.include_router(crud.router)
router.include_router(messages.router)
router.include_router(send.router)