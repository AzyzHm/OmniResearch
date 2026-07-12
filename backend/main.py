from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config.settings import get_settings

""" Import order matters here: the reranker (torch/sentence-transformers) must be imported BEFORE the route modules. Importing the routes first pulls in
the Gemini SDK (google-genai) and its native dependencies (grpc/protobuf); loading those before torch causes a native DLL collision that crashes the
process with an access violation (0xC0000005) on Windows. Loading torch first avoids it — confirmed by isolated reproduction during debugging.
Do not reorder these two import blocks without re-testing on Windows."""

from backend.services.embeddings import warm_up_embedding_model
from backend.services.reranker import warm_up_reranker

from backend.routes import auth_router, admin_router, projects_router, chats_router, collections_router, search_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    warm_up_embedding_model()
    warm_up_reranker()
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