"""
Tests for the context compressor.

Verifies that:
  - Sentences are correctly split
  - Compression reduces token count
  - At least one sentence is always kept per chunk
  - Token budget is respected
"""

import pytest
from unittest.mock import patch

from app.retrieval import compressor
from app.retrieval.compressor import _split_sentences, CompressedChunk


class TestSentenceSplitting:
    """Test the sentence splitting helper."""

    def test_basic_splitting(self):
        text = "This is sentence one. This is sentence two. This is sentence three."
        sentences = _split_sentences(text)
        assert len(sentences) == 3

    def test_newline_splitting(self):
        text = "Line one.\nLine two.\nLine three."
        sentences = _split_sentences(text)
        assert len(sentences) == 3

    def test_empty_text(self):
        sentences = _split_sentences("")
        assert sentences == []

    def test_single_sentence(self):
        text = "Just one sentence here."
        sentences = _split_sentences(text)
        assert len(sentences) == 1
        assert sentences[0] == "Just one sentence here."

    def test_preserves_content(self):
        text = "First sentence. Second sentence. Third sentence."
        sentences = _split_sentences(text)
        # All content should be preserved across sentences
        joined = " ".join(sentences)
        assert "First" in joined
        assert "Second" in joined
        assert "Third" in joined

    def test_mixed_punctuation(self):
        text = "Is this a question? Yes it is! And this is a statement."
        sentences = _split_sentences(text)
        assert len(sentences) >= 2  # At least 2 sentences


class TestBudgetConditionalCompression:
    """Compression must pass context through intact when it fits the budget.

    Regression guard for the 2026-09-01 diagnosis: sentence-level filtering
    below the token budget destroyed ground-truth evidence on 13/20 QA items
    while saving only ~90 tokens.
    """

    def test_under_budget_passes_through_without_scoring(self):
        chunks = [
            ("c1", "Sentence one about Starlette. Sentence two about Pydantic."),
            ("c2", "Another sentence here about Uvicorn."),
        ]
        with patch.object(
            compressor, "score_pairs",
            side_effect=AssertionError("filtering must not run under budget"),
        ):
            out = compressor.compress_context("query", chunks)

        assert [c.compressed_text for c in out] == [t for _, t in chunks]
        assert out[0].sentences_kept == out[0].sentences_total == 2
        assert out[0].compressed_token_count == out[0].original_token_count

    def test_over_budget_engages_filtering(self):
        chunks = [("c1", "A sentence. " * 50)]
        scores = [1.0] * 50
        with patch.object(compressor, "score_pairs", return_value=scores):
            out = compressor.compress_context("query", chunks, max_total_tokens=10)

        assert len(out) == 1
        assert out[0].compressed_token_count < out[0].original_token_count

    def test_over_budget_respects_total_token_cap(self):
        chunks = [("c1", "A sentence. " * 50), ("c2", "Another sentence. " * 50)]
        scores = [1.0] * 50
        with patch.object(compressor, "score_pairs", return_value=scores):
            out = compressor.compress_context("query", chunks, max_total_tokens=20)

        total = sum(c.compressed_token_count for c in out)
        assert total <= 20
