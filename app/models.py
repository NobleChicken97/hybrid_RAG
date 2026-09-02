"""
Pydantic schemas for API request/response models.

These define the contract for all FastAPI endpoints.
"""

from datetime import datetime
from pydantic import BaseModel, Field


# ─── Ingest ──────────────────────────────────────────────────────────────────

class IngestRequest(BaseModel):
    """Request body for POST /ingest."""
    title: str = Field(..., description="Document title")
    raw_text: str | None = Field(None, description="Raw text content (alternative to file upload)")


class ChunkPreview(BaseModel):
    """A preview of a single chunk (returned after ingestion)."""
    chunk_id: str
    text_preview: str = Field(..., description="First 200 characters of the chunk text")
    token_count: int
    section_header: str | None = None


class IngestResponse(BaseModel):
    """Response from POST /ingest."""
    doc_id: str
    title: str
    chunk_count: int
    sample_chunks: list[ChunkPreview]


# ─── Query ───────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    """Request body for POST /query."""
    question: str = Field(..., description="The question to answer")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of top results")
    mode: str = Field(
        default="hybrid",
        description="Retrieval mode: 'vector_only' or 'hybrid'",
    )


class Citation(BaseModel):
    """A citation linking an answer to a source chunk."""
    chunk_id: str
    doc_title: str
    snippet: str = Field(..., description="Relevant excerpt from the source chunk")
    source_path: str | None = None


class RetrievalHit(BaseModel):
    """A single retrieval hit with score."""
    chunk_id: str
    score: float
    text_preview: str


class RetrievalDebug(BaseModel):
    """Debug info showing the retrieval pipeline internals."""
    bm25_hits: list[RetrievalHit] = []
    vector_hits: list[RetrievalHit] = []
    fused_order: list[RetrievalHit] = []
    reranked_order: list[RetrievalHit] = []


class QueryResponse(BaseModel):
    """Response from POST /query."""
    answer: str
    citations: list[Citation]
    retrieval_debug: RetrievalDebug


# ─── Evaluation ──────────────────────────────────────────────────────────────

class QAItem(BaseModel):
    """A single QA evaluation item."""
    question: str
    ground_truth_answer: str
    ground_truth_chunk_ids: list[str] = []


class EvalRunRequest(BaseModel):
    """Request body for POST /eval/run."""
    qa_set_name: str = Field(default="default", description="Name of the QA set to evaluate")
    mode: str = Field(default="hybrid", description="Retrieval mode for this eval run")
    qa_items: list[QAItem] | None = Field(
        None, description="Inline QA items (overrides qa_set_name if provided)"
    )


class QuestionScore(BaseModel):
    """Per-question evaluation scores."""
    question: str
    answer: str
    faithfulness: float | None = None
    answer_relevancy: float | None = None
    context_precision: float | None = None
    context_recall: float | None = None


class EvalScores(BaseModel):
    """Aggregate evaluation scores."""
    faithfulness: float | None = None
    answer_relevancy: float | None = None
    context_precision: float | None = None
    context_recall: float | None = None


class EvalRunResponse(BaseModel):
    """Response from POST /eval/run."""
    run_id: str
    retrieval_mode: str
    timestamp: datetime
    scores: EvalScores
    per_question_breakdown: list[QuestionScore]


class EvalRunSummary(BaseModel):
    """Summary of an eval run (for listing)."""
    run_id: str
    retrieval_mode: str
    timestamp: datetime
    scores: EvalScores


# ─── Health ──────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    """Response from GET /health."""
    status: str = "ok"
    documents_count: int = 0
    chunks_count: int = 0
    eval_runs_count: int = 0
    environment: str = "local"
    llm_backend: str = "ollama_qwen3"
