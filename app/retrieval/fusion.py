"""
Reciprocal Rank Fusion (RRF) for merging ranked result lists.

RRF is a simple, effective fusion strategy used in production RAG systems
(Notion AI, Perplexity, enterprise search). It doesn't need score calibration
because it works purely on rank positions.

Formula:
    RRF_score(doc) = Σ 1 / (k + rank_i)  for each list i containing doc

Where k is a constant (typically 60) that smooths the contribution of rank.
"""

from dataclasses import dataclass


@dataclass
class FusedResult:
    """A result from RRF fusion."""
    chunk_id: str
    rrf_score: float
    text: str
    sources: list[str]  # Which retrieval methods returned this result


def fuse(
    bm25_results: list[tuple[str, float, str]],  # [(chunk_id, score, text)]
    vector_results: list[tuple[str, float, str]],  # [(chunk_id, score, text)]
    k: int = 60,
) -> list[FusedResult]:
    """
    Merge BM25 and vector search results using Reciprocal Rank Fusion.

    Args:
        bm25_results: Ranked BM25 results as (chunk_id, score, text) tuples.
        vector_results: Ranked vector search results as (chunk_id, score, text) tuples.
        k: RRF smoothing constant (standard = 60).

    Returns:
        Merged and re-ranked list of FusedResult objects, best first.
    """
    # Accumulate RRF scores per chunk
    rrf_scores: dict[str, float] = {}
    chunk_texts: dict[str, str] = {}
    chunk_sources: dict[str, list[str]] = {}

    # Process BM25 results
    for rank, (chunk_id, _score, text) in enumerate(bm25_results):
        rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + 1.0 / (k + rank + 1)
        chunk_texts[chunk_id] = text
        chunk_sources.setdefault(chunk_id, []).append("bm25")

    # Process vector results
    for rank, (chunk_id, _score, text) in enumerate(vector_results):
        rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + 1.0 / (k + rank + 1)
        chunk_texts[chunk_id] = text  # Vector text takes precedence if both have it
        chunk_sources.setdefault(chunk_id, []).append("vector")

    # Sort by RRF score (highest first)
    sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

    return [
        FusedResult(
            chunk_id=chunk_id,
            rrf_score=score,
            text=chunk_texts[chunk_id],
            sources=chunk_sources[chunk_id],
        )
        for chunk_id, score in sorted_results
    ]
