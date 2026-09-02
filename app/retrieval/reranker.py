"""
Cross-encoder reranker using ms-marco-MiniLM-L-6-v2.

Takes the fused candidate list from RRF and re-scores each chunk
against the query using a cross-encoder model. This produces much
more accurate relevance scores than embedding similarity alone.

Runs on CPU — small enough (~80MB) for the target hardware.
"""

from dataclasses import dataclass
from functools import lru_cache

from sentence_transformers import CrossEncoder

from app.config import get_settings


@dataclass
class RankedChunk:
    """A chunk with its cross-encoder relevance score."""
    chunk_id: str
    score: float
    text: str
    original_sources: list[str]  # 'bm25', 'vector', or both


@lru_cache(maxsize=1)
def _get_reranker() -> CrossEncoder:
    """Load and cache the cross-encoder model (singleton)."""
    settings = get_settings()
    print(f"[Reranker] Loading model: {settings.reranker_model}")
    model = CrossEncoder(settings.reranker_model)
    print("[Reranker] Model loaded.")
    return model


def rerank(
    query: str,
    candidates: list[tuple[str, str, list[str]]],  # [(chunk_id, text, sources)]
    top_n: int = 5,
) -> list[RankedChunk]:
    """
    Rerank candidate chunks using the cross-encoder.

    Args:
        query: The user's query.
        candidates: List of (chunk_id, text, sources) tuples from RRF fusion.
        top_n: Number of top results to return after reranking.

    Returns:
        Top-N RankedChunk objects sorted by cross-encoder score (best first).
    """
    if not candidates:
        return []

    reranker = _get_reranker()

    # Cross-encoder expects (query, passage) pairs
    pairs = [(query, text) for _, text, _ in candidates]

    # Score all pairs
    scores = reranker.predict(pairs)

    # Zip scores with candidates and sort
    scored = [
        RankedChunk(
            chunk_id=chunk_id,
            score=float(score),
            text=text,
            original_sources=sources,
        )
        for (chunk_id, text, sources), score in zip(candidates, scores, strict=True)
    ]

    # Sort by cross-encoder score (highest = most relevant)
    scored.sort(key=lambda x: x.score, reverse=True)

    return scored[:top_n]


def score_pairs(query: str, texts: list[str]) -> list[float]:
    """
    Score query-text pairs without ranking.

    Useful for context compression (scoring individual sentences).

    Args:
        query: The query.
        texts: List of text passages to score.

    Returns:
        List of relevance scores (same order as input texts).
    """
    if not texts:
        return []

    reranker = _get_reranker()
    pairs = [(query, text) for text in texts]
    scores = reranker.predict(pairs)
    return [float(s) for s in scores]
