"""
Context compression: trim retrieved chunks to relevant spans.

Instead of dumping full 512-token chunks into the LLM prompt, we:
  1. Split each chunk into sentences
  2. Score each sentence against the query using the cross-encoder
  3. Keep only sentences above a relevance threshold
  4. Reconstruct a trimmed chunk with the relevant spans

This reduces prompt token usage and improves answer quality by
removing noisy context that could distract the LLM.
"""

import re
from dataclasses import dataclass

from app.config import get_settings
from app.retrieval.reranker import score_pairs


@dataclass
class CompressedChunk:
    """A chunk trimmed to its relevant spans."""
    chunk_id: str
    original_text: str
    compressed_text: str
    original_token_count: int
    compressed_token_count: int
    sentences_kept: int
    sentences_total: int


def _split_sentences(text: str) -> list[str]:
    """
    Split text into sentences using regex.

    Handles common abbreviations and decimal numbers to avoid false splits.
    """
    # Split on sentence-ending punctuation followed by whitespace
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)

    # Further split on newlines (common in markdown)
    result = []
    for sent in sentences:
        parts = sent.split("\n")
        for part in parts:
            part = part.strip()
            if part:
                result.append(part)

    return result


def compress_context(
    query: str,
    chunks: list[tuple[str, str]],  # [(chunk_id, text)]
    threshold: float | None = None,
    max_total_tokens: int | None = None,
) -> list[CompressedChunk]:
    """
    Compress chunks by keeping only relevant sentences.

    Args:
        query: The user's query.
        chunks: List of (chunk_id, text) tuples to compress.
        threshold: Minimum cross-encoder score for a sentence to be kept.
                   Defaults to config.compression_threshold.
        max_total_tokens: Maximum total tokens across all compressed chunks.
                          Defaults to config.max_context_tokens.

    Returns:
        List of CompressedChunk objects with trimmed text.
    """
    settings = get_settings()
    if threshold is None:
        threshold = settings.compression_threshold
    if max_total_tokens is None:
        max_total_tokens = settings.max_context_tokens

    from app.ingestion.chunker import count_tokens

    # Budget-conditional compression: when the full retrieved context fits the
    # token budget, pass it through intact. Sentence-level filtering below the
    # budget only destroys evidence — the sentence containing the answer often
    # does not restate the query's keywords (diagnosed 2026-09-01: threshold-
    # agnostic evidence loss on 13/20 QA items, for ~90 tokens saved).
    full_total_tokens = sum(count_tokens(text) for _, text in chunks)
    if full_total_tokens <= max_total_tokens:
        compressed_chunks = []
        for chunk_id, text in chunks:
            sentences = _split_sentences(text)
            compressed_chunks.append(
                CompressedChunk(
                    chunk_id=chunk_id,
                    original_text=text,
                    compressed_text=text,
                    original_token_count=count_tokens(text),
                    compressed_token_count=count_tokens(text),
                    sentences_kept=len(sentences),
                    sentences_total=len(sentences),
                )
            )
        return compressed_chunks

    compressed_chunks = []
    total_tokens = 0

    for chunk_id, text in chunks:
        sentences = _split_sentences(text)

        if not sentences:
            continue

        # Score each sentence against the query
        scores = score_pairs(query, sentences)

        # Keep sentences above threshold
        kept_sentences = [
            sent
            for sent, score in zip(sentences, scores)
            if score >= threshold
        ]

        # If nothing survived the threshold, keep the highest-scored sentence
        if not kept_sentences and sentences:
            best_idx = scores.index(max(scores))
            kept_sentences = [sentences[best_idx]]

        compressed_text = " ".join(kept_sentences)
        compressed_tokens = count_tokens(compressed_text)

        # Check total token budget
        if total_tokens + compressed_tokens > max_total_tokens:
            # Truncate to fit budget
            remaining_budget = max_total_tokens - total_tokens
            if remaining_budget <= 0:
                break
            # Take as many sentences as fit
            truncated = []
            running_tokens = 0
            for sent in kept_sentences:
                sent_tokens = count_tokens(sent)
                if running_tokens + sent_tokens > remaining_budget:
                    break
                truncated.append(sent)
                running_tokens += sent_tokens
            if not truncated:
                break
            compressed_text = " ".join(truncated)
            compressed_tokens = count_tokens(compressed_text)

        total_tokens += compressed_tokens

        compressed_chunks.append(
            CompressedChunk(
                chunk_id=chunk_id,
                original_text=text,
                compressed_text=compressed_text,
                original_token_count=count_tokens(text),
                compressed_token_count=compressed_tokens,
                sentences_kept=len(kept_sentences),
                sentences_total=len(sentences),
            )
        )

    return compressed_chunks
