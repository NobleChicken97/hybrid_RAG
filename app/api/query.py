"""
POST /query — Question answering endpoint.

Supports two modes:
  - "vector_only": Embed query → ChromaDB search → LLM
  - "hybrid" (default): Embed query → parallel vector + BM25 → RRF fusion
    → cross-encoder rerank → context compression → LLM
"""

from fastapi import APIRouter, HTTPException

from app.generation.citations import build_citation_map, get_citations_for_answer
from app.generation.llm import generate
from app.generation.prompt import SYSTEM_PROMPT, build_prompt
from app.models import (
    QueryRequest,
    QueryResponse,
    RetrievalDebug,
    RetrievalHit,
)
from app.retrieval import vector_store
from app.retrieval.pipeline import run_retrieval_pipeline

router = APIRouter(tags=["Query"])


@router.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """
    Answer a question using the hybrid retrieval pipeline.

    Pipeline (hybrid mode):
      1. Embed query → vector search (top-K)
      2. BM25 search (top-K)
      3. RRF fusion → merged candidates
      4. Cross-encoder rerank → top-N
      5. Context compression → trimmed spans
      6. Prompt assembly → LLM → answer + citations

    Retrieval itself lives in `app.retrieval.pipeline` (shared with the
    evaluation harness).
    """
    question = request.question.strip()

    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # Check if we have any documents
    if vector_store.get_chunk_count() == 0:
        raise HTTPException(
            status_code=400,
            detail="No documents ingested yet. Use POST /ingest first.",
        )

    # --- Retrieval: shared pipeline (embed → vector/BM25 → RRF → rerank → compress) ---
    pipeline = run_retrieval_pipeline(question, mode=request.mode, top_n=request.top_k)

    vector_hits = [
        RetrievalHit(chunk_id=r.chunk_id, score=r.score, text_preview=r.text[:150])
        for r in pipeline.vector_results
    ]
    bm25_hits = [
        RetrievalHit(chunk_id=r.chunk_id, score=r.score, text_preview=r.text[:150])
        for r in pipeline.bm25_results
    ]
    if pipeline.fused_results:
        fused_hits = [
            RetrievalHit(chunk_id=r.chunk_id, score=r.rrf_score, text_preview=r.text[:150])
            for r in pipeline.fused_results
        ]
    else:
        fused_hits = vector_hits.copy()
    reranked_hits = [
        RetrievalHit(chunk_id=r.chunk_id, score=r.score, text_preview=r.text[:150])
        for r in pipeline.reranked
    ]

    if not pipeline.reranked:
        return QueryResponse(
            answer="No relevant chunks found for this question.",
            citations=[],
            retrieval_debug=RetrievalDebug(
                bm25_hits=bm25_hits,
                vector_hits=vector_hits,
                fused_order=fused_hits,
                reranked_order=[],
            ),
        )

    # --- Build prompt and generate ---
    context_for_prompt = [
        (chunk_id, text, doc_title) for chunk_id, text, doc_title, _ in pipeline.contexts
    ]
    context_for_citations = list(pipeline.contexts)

    # Build prompt
    user_prompt = build_prompt(question, context_for_prompt)

    # Generate answer
    answer = generate(user_prompt, system_prompt=SYSTEM_PROMPT)

    # --- Step 7: Extract citations ---
    citation_map = build_citation_map(context_for_citations)
    citations = get_citations_for_answer(answer, citation_map)

    return QueryResponse(
        answer=answer,
        citations=citations,
        retrieval_debug=RetrievalDebug(
            bm25_hits=bm25_hits,
            vector_hits=vector_hits,
            fused_order=fused_hits,
            reranked_order=reranked_hits,
        ),
    )
