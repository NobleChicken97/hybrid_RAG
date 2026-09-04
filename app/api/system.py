"""
System introspection endpoints (read-only, no secrets).

GET /documents — list ingested documents with chunk counts (no chunk text).
GET /config    — safe pipeline config snapshot for the System/Topology pages.
                 Never includes API keys or base URLs.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import Chunk, Document, get_db

router = APIRouter(tags=["System"])


@router.get("/documents")
async def list_documents(db: Session = Depends(get_db)):
    """List ingested documents with per-document chunk counts."""
    counts = dict(
        db.query(Chunk.doc_id, func.count(Chunk.id)).group_by(Chunk.doc_id).all()
    )
    docs = db.query(Document).order_by(Document.ingested_at.desc()).all()
    return [
        {
            "doc_id": d.doc_id,
            "title": d.title,
            "source_path": d.source_path,
            "chunk_count": counts.get(d.doc_id, 0),
            "ingested_at": d.ingested_at.isoformat() if d.ingested_at else None,
        }
        for d in docs
    ]


@router.get("/config")
async def get_public_config():
    """Safe pipeline config snapshot (keys and model names only)."""
    settings = get_settings()
    generation_models = {
        "cerebras": settings.cerebras_model,
        "groq": settings.groq_model,
        "gemini": settings.gemini_model,
        "claude": "claude-3-haiku",
        "ollama_qwen3": settings.ollama_model_primary,
        "ollama_phi4mini": settings.ollama_model_secondary,
    }
    return {
        "environment": settings.environment,
        "llm_backend": settings.llm_backend,
        "generation_model": generation_models.get(settings.llm_backend),
        "judge_backend": settings.ragas_judge_backend,
        "judge_model": settings.ragas_judge_model,
        "embedding_model": settings.embedding_model,
        "reranker_model": settings.reranker_model,
        "retrieval_top_k": settings.retrieval_top_k,
        "rerank_top_n": settings.rerank_top_n,
        "rrf_k": settings.rrf_k,
        "compression_threshold": settings.compression_threshold,
        "max_context_tokens": settings.max_context_tokens,
    }
