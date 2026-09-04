"""
Shared retrieval pipeline (single source of truth).

Previously cloned in `app/api/query.py` and `app/evaluation/harness.py`
(~50 lines each, diverged only in how they shaped the output). Both callers
now use `run_retrieval_pipeline` and map its result to their own response
shapes, so a retrieval change can never fix one path and break the other.

Stages: embed → vector search (+ BM25 → RRF fusion in hybrid mode) →
cross-encoder rerank → budget-conditional compression → metadata lookup.

The metadata lookup is a SINGLE batched `get_chunks_by_ids` call: the old
code issued one Chroma round-trip per chunk (N+1).
"""

from dataclasses import dataclass, field

from app.config import get_settings
from app.ingestion.embedder import embed_query
from app.retrieval import bm25_index, vector_store
from app.retrieval.bm25_index import BM25SearchResult
from app.retrieval.compressor import CompressedChunk, compress_context
from app.retrieval.fusion import FusedResult, fuse
from app.retrieval.reranker import RankedChunk, rerank
from app.retrieval.vector_store import VectorSearchResult


@dataclass
class PipelineResult:
    """Everything both callers need; each maps it to its own response shape."""

    vector_results: list[VectorSearchResult] = field(default_factory=list)
    bm25_results: list[BM25SearchResult] = field(default_factory=list)
    # Empty in vector_only mode or when BM25 returns nothing (same rule as before).
    fused_results: list[FusedResult] = field(default_factory=list)
    reranked: list[RankedChunk] = field(default_factory=list)
    compressed: list[CompressedChunk] = field(default_factory=list)
    # [(chunk_id, compressed_text, doc_title, source_path)] in rerank order.
    contexts: list[tuple[str, str, str, str | None]] = field(default_factory=list)


def run_retrieval_pipeline(
    question: str,
    mode: str = "hybrid",
    top_n: int | None = None,
) -> PipelineResult:
    """
    Run retrieval + rerank + compression for one question.

    Args:
        question: The user's question.
        mode: 'hybrid' (vector + BM25 → RRF → rerank) or anything else
            (vector only — same convention the old call sites used).
        top_n: Reranked chunks to keep. Defaults to config.rerank_top_n.

    Returns:
        PipelineResult with every intermediate stage for debug/scoring.
    """
    settings = get_settings()
    if top_n is None:
        top_n = settings.rerank_top_n

    result = PipelineResult()

    # --- Vector search (both modes) ---
    query_embedding = embed_query(question)
    result.vector_results = vector_store.search(
        query_embedding, top_k=settings.retrieval_top_k
    )

    # --- BM25 + RRF fusion (hybrid only) ---
    if mode == "hybrid":
        result.bm25_results = bm25_index.search(
            question, top_k=settings.retrieval_top_k
        )

    if mode == "hybrid" and result.bm25_results:
        result.fused_results = fuse(
            bm25_results=[(r.chunk_id, r.score, r.text) for r in result.bm25_results],
            vector_results=[(r.chunk_id, r.score, r.text) for r in result.vector_results],
            k=settings.rrf_k,
        )
        candidates = [(r.chunk_id, r.text, r.sources) for r in result.fused_results]
    else:
        candidates = [(r.chunk_id, r.text, ["vector"]) for r in result.vector_results]

    # --- Cross-encoder rerank ---
    result.reranked = rerank(
        question, candidates[: settings.retrieval_top_k], top_n=top_n
    )
    if not result.reranked:
        return result

    # --- Context compression ---
    result.compressed = compress_context(
        question, [(r.chunk_id, r.text) for r in result.reranked]
    )

    # --- Metadata: ONE batched lookup for all chunks (was N+1) ---
    metas: dict[str, dict] = {}
    if result.compressed:
        for row in vector_store.get_chunks_by_ids(
            [c.chunk_id for c in result.compressed]
        ):
            metas[row.chunk_id] = row.metadata
    for comp in result.compressed:
        meta = metas.get(comp.chunk_id, {})
        result.contexts.append(
            (
                comp.chunk_id,
                comp.compressed_text,
                meta.get("doc_title", "Unknown"),
                meta.get("source_path"),
            )
        )

    return result
