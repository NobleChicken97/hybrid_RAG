"""
POST /query — Question answering endpoint.

Supports two modes:
  - "vector_only": Embed query → ChromaDB search → LLM
  - "hybrid" (default): Embed query → parallel vector + BM25 → RRF fusion
    → cross-encoder rerank → context compression → LLM
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db, Chunk
from app.models import (
    QueryRequest, QueryResponse, Citation, RetrievalDebug, RetrievalHit,
)
from app.ingestion.embedder import embed_query
from app.retrieval import vector_store, bm25_index
from app.retrieval.fusion import fuse
from app.retrieval.reranker import rerank
from app.retrieval.compressor import compress_context
from app.generation.llm import generate
from app.generation.prompt import build_prompt, SYSTEM_PROMPT
from app.generation.citations import build_citation_map, get_citations_for_answer

router = APIRouter(tags=["Query"])


@router.post("/query", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    db: Session = Depends(get_db),
):
    """
    Answer a question using the hybrid retrieval pipeline.

    Pipeline (hybrid mode):
      1. Embed query → vector search (top-K)
      2. BM25 search (top-K)
      3. RRF fusion → merged candidates
      4. Cross-encoder rerank → top-N
      5. Context compression → trimmed spans
      6. Prompt assembly → Claude → answer + citations
    """
    settings = get_settings()
    question = request.question.strip()

    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # Check if we have any documents
    if vector_store.get_chunk_count() == 0:
        raise HTTPException(
            status_code=400,
            detail="No documents ingested yet. Use POST /ingest first.",
        )

    # --- Step 1: Vector search ---
    query_embedding = embed_query(question)
    vector_results = vector_store.search(query_embedding, top_k=settings.retrieval_top_k)

    vector_hits = [
        RetrievalHit(
            chunk_id=r.chunk_id,
            score=r.score,
            text_preview=r.text[:150],
        )
        for r in vector_results
    ]

    # --- Step 2: BM25 search (only in hybrid mode) ---
    bm25_hits = []
    if request.mode == "hybrid":
        bm25_results = bm25_index.search(question, top_k=settings.retrieval_top_k)
        bm25_hits = [
            RetrievalHit(
                chunk_id=r.chunk_id,
                score=r.score,
                text_preview=r.text[:150],
            )
            for r in bm25_results
        ]

    # --- Step 3: Fusion (or pass-through for vector_only) ---
    if request.mode == "hybrid" and bm25_results:
        fused_results = fuse(
            bm25_results=[(r.chunk_id, r.score, r.text) for r in bm25_results],
            vector_results=[(r.chunk_id, r.score, r.text) for r in vector_results],
            k=settings.rrf_k,
        )
        fused_hits = [
            RetrievalHit(
                chunk_id=r.chunk_id,
                score=r.rrf_score,
                text_preview=r.text[:150],
            )
            for r in fused_results
        ]
        candidates_for_rerank = [
            (r.chunk_id, r.text, r.sources) for r in fused_results
        ]
    else:
        fused_hits = vector_hits.copy()
        candidates_for_rerank = [
            (r.chunk_id, r.text, ["vector"]) for r in vector_results
        ]

    # --- Step 4: Cross-encoder reranking ---
    reranked = rerank(
        query=question,
        candidates=candidates_for_rerank[:settings.retrieval_top_k],
        top_n=request.top_k,
    )

    reranked_hits = [
        RetrievalHit(
            chunk_id=r.chunk_id,
            score=r.score,
            text_preview=r.text[:150],
        )
        for r in reranked
    ]

    if not reranked:
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

    # --- Step 5: Context compression ---
    chunks_for_compression = [(r.chunk_id, r.text) for r in reranked]
    compressed = compress_context(question, chunks_for_compression)

    # --- Step 6: Build prompt and generate ---
    # Look up doc titles from metadata
    context_for_prompt = []
    context_for_citations = []

    for comp in compressed:
        # Get metadata from vector store
        chunk_meta = vector_store.get_chunks_by_ids([comp.chunk_id])
        doc_title = "Unknown"
        source_path = None
        if chunk_meta:
            doc_title = chunk_meta[0].metadata.get("doc_title", "Unknown")
            source_path = chunk_meta[0].metadata.get("source_path")

        context_for_prompt.append((comp.chunk_id, comp.compressed_text, doc_title))
        context_for_citations.append((comp.chunk_id, comp.compressed_text, doc_title, source_path))

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
