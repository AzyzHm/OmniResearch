from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config.settings import get_settings
from backend.routes import auth_router, admin_router, projects_router, chats_router, collections_router

settings = get_settings()

app = FastAPI(
    title="OmniResearch API",
    description="Authentication & Administration backend for OmniResearch",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    expose_headers=["Content-Length"],
    max_age=600,
)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(projects_router)
app.include_router(chats_router)
app.include_router(collections_router)


@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "ok",
        "service": "OmniResearch API",
        "cors_origins": settings.cors_origins_list,
    }