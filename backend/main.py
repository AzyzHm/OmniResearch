from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config.settings import get_settings
from backend.routes import auth_router, admin_router, projects_router, chats_router, collections_router, search_router
from backend.services.embeddings import warm_up_embedding_model

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    warm_up_embedding_model()
    yield


app = FastAPI(
    title="OmniResearch API",
    description="Authentication & Administration backend for OmniResearch",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    expose_headers=["Content-Length"],
    max_age=600,
)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(projects_router)
app.include_router(chats_router)
app.include_router(collections_router)
app.include_router(search_router)


@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "ok",
        "service": "OmniResearch API",
        "cors_origins": settings.cors_origins_list,
    }