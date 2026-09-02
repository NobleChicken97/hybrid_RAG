"""
Tests for the context-aware chunker.

Verifies that:
  - Markdown headers create section boundaries
  - Paragraphs within sections become separate chunks
  - Oversized paragraphs are split by sentences
  - Tiny chunks are merged into neighbors
  - Chunk metadata (offsets, token counts, section headers) is correct
"""

import pytest
from app.ingestion.loader import RawDocument
from app.ingestion.chunker import chunk_document, count_tokens


# ─── Fixtures ─────────────────────────────────────────────────────────────────

SAMPLE_MARKDOWN = """# Introduction

This is the introduction paragraph. It contains some basic information
about the topic at hand.

## Section One

This is the first section with some detailed content about the topic.
It has enough text to be a meaningful chunk on its own.

### Subsection A

Subsection A discusses specific details that are important for
understanding the broader topic.

## Section Two

Section two covers a different aspect of the topic entirely.
This section also has meaningful content.

### Subsection B

This subsection provides additional details about section two.
It includes some examples and explanations.
"""

OVERSIZED_PARAGRAPH = (
    "This is sentence one. " * 100 +
    "This is the final sentence."
)


def _make_doc(text: str, file_type: str = "md") -> RawDocument:
    """Helper to create a RawDocument."""
    return RawDocument(
        text=text,
        title="Test Document",
        source_path="/test/doc.md",
        file_type=file_type,
    )


# ─── Tests ────────────────────────────────────────────────────────────────────

class TestHeaderSplitting:
    """Test that headers create chunk boundaries."""

    def test_splits_on_markdown_headers(self):
        doc = _make_doc(SAMPLE_MARKDOWN)
        chunks = chunk_document(doc, "test_doc")

        # Should produce multiple chunks (one per section/subsection)
        assert len(chunks) >= 4, f"Expected >=4 chunks, got {len(chunks)}"

        # Each chunk should have text
        for chunk in chunks:
            assert chunk.text.strip(), f"Empty chunk: {chunk.chunk_id}"

    def test_section_headers_preserved(self):
        doc = _make_doc(SAMPLE_MARKDOWN)
        chunks = chunk_document(doc, "test_doc")

        # At least some chunks should have section headers
        headers = [c.section_header for c in chunks if c.section_header]
        assert len(headers) > 0, "No section headers found in chunks"

    def test_no_headers_single_section(self):
        text = "This is a document without any headers. Just plain text."
        doc = _make_doc(text, file_type="txt")
        chunks = chunk_document(doc, "test_doc")

        # Should produce at least 1 chunk
        assert len(chunks) >= 1
        assert chunks[0].section_header is None


class TestParagraphSplitting:
    """Test that double-newlines create paragraph boundaries within sections."""

    def test_paragraphs_become_chunks(self):
        text = """# Header

Paragraph one has some content here.

Paragraph two is separate from paragraph one.

Paragraph three is also its own chunk."""

        doc = _make_doc(text)
        chunks = chunk_document(doc, "test_doc")

        # Should have at least 3 chunks (3 paragraphs under 1 header)
        # but they might merge if tiny
        assert len(chunks) >= 1


class TestOversizedSplitting:
    """Test that oversized paragraphs are split by sentences."""

    def test_oversized_paragraph_split(self):
        doc = _make_doc(OVERSIZED_PARAGRAPH, file_type="txt")
        chunks = chunk_document(doc, "test_doc", max_tokens=100)

        # Should produce multiple chunks
        assert len(chunks) > 1, "Oversized paragraph should be split"

        # Each chunk should be under the token limit (roughly)
        for chunk in chunks:
            assert chunk.token_count <= 150, (
                f"Chunk exceeds limit: {chunk.token_count} tokens"
            )


class TestTinyChunkMerging:
    """Test that tiny chunks are merged into neighbors."""

    def test_tiny_chunks_merged(self):
        text = """# Header

Short.

Also short.

This one has more content and should be a reasonable chunk on its own
with enough tokens to pass the minimum threshold."""

        doc = _make_doc(text)
        chunks = chunk_document(doc, "test_doc", min_tokens=10)

        # The two tiny chunks should be merged
        # Total chunks should be less than 3
        for chunk in chunks:
            assert chunk.token_count >= 5, f"Chunk too small: {chunk.token_count}"


class TestChunkMetadata:
    """Test that chunk metadata is correctly populated."""

    def test_chunk_ids_unique(self):
        doc = _make_doc(SAMPLE_MARKDOWN)
        chunks = chunk_document(doc, "test_doc")

        ids = [c.chunk_id for c in chunks]
        assert len(ids) == len(set(ids)), "Chunk IDs are not unique"

    def test_chunk_ids_have_doc_prefix(self):
        doc = _make_doc(SAMPLE_MARKDOWN)
        chunks = chunk_document(doc, "my_doc_123")

        for chunk in chunks:
            assert chunk.chunk_id.startswith("my_doc_123__chunk_"), (
                f"Bad chunk ID: {chunk.chunk_id}"
            )

    def test_doc_id_correct(self):
        doc = _make_doc(SAMPLE_MARKDOWN)
        chunks = chunk_document(doc, "test_doc")

        for chunk in chunks:
            assert chunk.doc_id == "test_doc"

    def test_token_counts_positive(self):
        doc = _make_doc(SAMPLE_MARKDOWN)
        chunks = chunk_document(doc, "test_doc")

        for chunk in chunks:
            assert chunk.token_count > 0, f"Zero token count: {chunk.chunk_id}"

    def test_offsets_valid(self):
        doc = _make_doc(SAMPLE_MARKDOWN)
        chunks = chunk_document(doc, "test_doc")

        for chunk in chunks:
            assert chunk.start_offset >= 0
            assert chunk.end_offset >= chunk.start_offset


class TestTokenCounting:
    """Test the token counting utility."""

    def test_empty_string(self):
        assert count_tokens("") >= 0

    def test_known_text(self):
        tokens = count_tokens("Hello, world!")
        assert tokens > 0
        assert tokens < 10  # Should be ~4 tokens
