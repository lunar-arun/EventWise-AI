from contextlib import asynccontextmanager
from typing import Any
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database.session import SessionLocal, init_db
from app.rag.embeddings import get_embedding_service
from app.rag.generation import get_generation_service
from app.routes import budget, chatbot, events, knowledge, planner, timeline
from app.services.seed_service import seed_initial_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if settings.SEED_SAMPLE_DATA_ON_STARTUP:
        db = SessionLocal()
        try:
            seed_initial_data(db)
        except Exception:
            pass
        finally:
            db.close()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Local-first Smart Event Planning Assistant powered by custom Python RAG, "
        "Sentence Transformers embeddings, ChromaDB vector search, SQLite persistence, "
        "and local Ollama inference."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def safe_global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Never expose internal stack traces or sensitive local paths to clients
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected server error occurred while processing your request.",
            "error_type": type(exc).__name__,
        },
    )


@app.get("/api/health", tags=["Health"])
def get_health() -> dict[str, Any]:
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "local_only": True,
        "embedding_model": get_embedding_service().model_name,
        "ollama_model": settings.OLLAMA_MODEL,
        "monetary_representation": "integer_inr",
    }


@app.get("/api/health/llm", tags=["Health"])
def get_llm_health() -> dict[str, Any]:
    return get_generation_service().check_health()


app.include_router(events.router)
app.include_router(planner.router)
app.include_router(budget.router)
app.include_router(timeline.router)
app.include_router(chatbot.router)
app.include_router(knowledge.router)
