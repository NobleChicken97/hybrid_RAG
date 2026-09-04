"""
FastAPI application entry point for the Hybrid RAG System.

Registers all API routers, configures CORS, and initializes
the database on startup.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.eval import router as eval_router
from app.api.ingest import router as ingest_router
from app.api.query import router as query_router
from app.api.system import router as system_router
from app.config import get_settings
from app.database import Chunk, Document, EvalRun, get_session_factory, init_db
from app.models import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # --- Startup ---
    print("=" * 60)
    print("  Hybrid RAG System — Starting up")
    print("=" * 60)

    settings = get_settings()

    # Create data directories
    settings.chroma_db_abs_path.mkdir(parents=True, exist_ok=True)
    settings.bm25_index_abs_path.mkdir(parents=True, exist_ok=True)
    settings.qa_sets_abs_path.mkdir(parents=True, exist_ok=True)
    settings.upload_abs_path.mkdir(parents=True, exist_ok=True)

    # Initialize database
    init_db()

    print(f"  LLM Backend:    {settings.llm_backend}")
    print(f"  Embedding Model: {settings.embedding_model}")
    print(f"  Reranker Model:  {settings.reranker_model}")
    print(f"  ChromaDB Path:   {settings.chroma_db_abs_path}")
    print(f"  SQLite Path:     {settings.sqlite_db_abs_path}")
    print("=" * 60)

    yield

    # --- Shutdown ---
    print("\nHybrid RAG System — Shutting down.")


# ─── App ─────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Hybrid RAG System",
    description=(
        "A hybrid retrieval-augmented generation system with BM25 + vector search, "
        "cross-encoder reranking, context compression, citations, and RAGAS evaluation."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to Streamlit origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(ingest_router)
app.include_router(query_router)
app.include_router(eval_router)
app.include_router(system_router)


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check with document/chunk/eval counts."""
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        docs = db.query(Document).count()
        chunks = db.query(Chunk).count()
        evals = db.query(EvalRun).count()
        settings = get_settings()
        return HealthResponse(
            status="ok",
            documents_count=docs,
            chunks_count=chunks,
            eval_runs_count=evals,
            environment=settings.environment,
            llm_backend=settings.llm_backend,
        )
    finally:
        db.close()
