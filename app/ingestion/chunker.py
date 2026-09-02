"""
Context-aware document chunker.

Strategy (per master guide):
  1. Split on header boundaries (# / ## / ### for markdown, line-pattern heuristics for plain text)
  2. Within each section, split on paragraph boundaries (double newlines)
  3. Apply a hard token-count cap ONLY for oversized paragraphs (last resort)
  4. Minimal overlap (1 trailing sentence carried to the next chunk at size-split boundaries)

This is NOT fixed-size sliding window chunking. Structure-first, size-last.
"""

import re
from dataclasses import dataclass

import tiktoken

from app.ingestion.loader import RawDocument


@dataclass
class TextChunk:
    """A text chunk ready for embedding."""
    chunk_id: str
    doc_id: str
    text: str
    start_offset: int
    end_offset: int
    token_count: int
    section_header: str | None = None


# ─── Tokenizer ───────────────────────────────────────────────────────────────

# Use cl100k_base (GPT-4 / Claude tokenizer approximation) for token counting.
# This is only for sizing — not for the actual LLM call.
try:
    _tokenizer = tiktoken.get_encoding("cl100k_base")
except Exception:
    _tokenizer = None


def count_tokens(text: str) -> int:
    """Count tokens using tiktoken, falling back to word-count heuristic."""
    if _tokenizer is not None:
        return len(_tokenizer.encode(text))
    # Rough fallback: ~1 token per 4 characters
    return max(1, len(text) // 4)


# ─── Header Detection ────────────────────────────────────────────────────────

# Markdown headers: # Title, ## Subtitle, ### Subsection
_MD_HEADER_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

# Plain text heuristic: ALL-CAPS lines, or lines followed by === or ---
_PLAIN_HEADER_PATTERNS = [
    re.compile(r"^([A-Z][A-Z\s\-:]{5,})$", re.MULTILINE),           # ALL CAPS lines
    re.compile(r"^(.+)\n[=]{3,}$", re.MULTILINE),                     # Underline with ===
    re.compile(r"^(.+)\n[-]{3,}$", re.MULTILINE),                     # Underline with ---
]


def _split_on_headers_md(text: str) -> list[tuple[str | None, str, int]]:
    """
    Split markdown text on headers.

    Returns list of (header_text, section_body, start_offset).
    """
    sections = []
    matches = list(_MD_HEADER_PATTERN.finditer(text))

    if not matches:
        # No headers found — treat entire text as one section
        return [(None, text, 0)]

    # Content before the first header
    if matches[0].start() > 0:
        pre_header = text[: matches[0].start()].strip()
        if pre_header:
            sections.append((None, pre_header, 0))

    for i, match in enumerate(matches):
        header = match.group(0).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if body:
            sections.append((header, body, match.start()))

    return sections


def _split_on_headers_plain(text: str) -> list[tuple[str | None, str, int]]:
    """
    Split plain text on detected header-like patterns.

    Falls back to returning the whole text as one section if no patterns match.
    """
    # Collect all potential header positions
    header_positions = []
    for pattern in _PLAIN_HEADER_PATTERNS:
        for match in pattern.finditer(text):
            header_positions.append((match.start(), match.end(), match.group(0).strip()))

    if not header_positions:
        return [(None, text, 0)]

    # Sort by position
    header_positions.sort(key=lambda x: x[0])

    sections = []

    # Content before the first header
    if header_positions[0][0] > 0:
        pre = text[: header_positions[0][0]].strip()
        if pre:
            sections.append((None, pre, 0))

    for i, (start, end, header) in enumerate(header_positions):
        next_start = header_positions[i + 1][0] if i + 1 < len(header_positions) else len(text)
        body = text[end:next_start].strip()
        if body:
            sections.append((header, body, start))

    return sections


# ─── Paragraph Splitting ─────────────────────────────────────────────────────

def _split_paragraphs(text: str) -> list[str]:
    """Split text on double-newline paragraph boundaries."""
    paragraphs = re.split(r"\n\s*\n", text)
    return [p.strip() for p in paragraphs if p.strip()]


# ─── Size-Based Splitting (Last Resort) ──────────────────────────────────────

def _split_oversized(text: str, max_tokens: int = 512, overlap_sentences: int = 1) -> list[str]:
    """
    Split an oversized paragraph by sentences with minimal overlap.

    Only used when a paragraph exceeds max_tokens after structure-aware splitting.
    """
    # Split on sentence boundaries
    sentences = re.split(r"(?<=[.!?])\s+", text)
    if not sentences:
        return [text]

    chunks = []
    current_chunk: list[str] = []
    current_tokens = 0

    for sentence in sentences:
        sentence_tokens = count_tokens(sentence)

        if current_tokens + sentence_tokens > max_tokens and current_chunk:
            # Emit current chunk
            chunks.append(" ".join(current_chunk))

            # Overlap: carry the last N sentences
            if overlap_sentences > 0:
                current_chunk = current_chunk[-overlap_sentences:]
                current_tokens = sum(count_tokens(s) for s in current_chunk)
            else:
                current_chunk = []
                current_tokens = 0

        current_chunk.append(sentence)
        current_tokens += sentence_tokens

    # Emit remaining
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


# ─── Main Chunker ────────────────────────────────────────────────────────────

def chunk_document(
    doc: RawDocument,
    doc_id: str,
    max_tokens: int = 512,
    min_tokens: int = 30,
) -> list[TextChunk]:
    """
    Context-aware chunking pipeline:
      1. Split on headers (structure-first)
      2. Split each section on paragraph boundaries
      3. Size-cap oversized paragraphs (last resort)
      4. Merge tiny paragraphs into their neighbors

    Args:
        doc: The loaded document to chunk.
        doc_id: The document ID to associate with chunks.
        max_tokens: Hard cap per chunk (only applied to oversized paragraphs).
        min_tokens: Minimum tokens for a chunk (tiny ones get merged).

    Returns:
        List of TextChunk objects ready for embedding.
    """
    text = doc.text

    # Step 1: Split on headers based on file type
    if doc.file_type == "md":
        sections = _split_on_headers_md(text)
    else:
        sections = _split_on_headers_plain(text)

    # Step 2 & 3: Split each section into paragraphs, then size-cap
    raw_chunks: list[tuple[str | None, str]] = []

    for header, body, _offset in sections:
        paragraphs = _split_paragraphs(body)

        for para in paragraphs:
            para_tokens = count_tokens(para)

            if para_tokens <= max_tokens:
                raw_chunks.append((header, para))
            else:
                # Oversized paragraph — split by sentences (last resort)
                sub_chunks = _split_oversized(para, max_tokens=max_tokens)
                for sub in sub_chunks:
                    raw_chunks.append((header, sub))

    # Step 4: Merge tiny chunks into neighbors
    merged_chunks: list[tuple[str | None, str]] = []
    for header, chunk_text in raw_chunks:
        if (
            merged_chunks
            and count_tokens(chunk_text) < min_tokens
            and merged_chunks[-1][0] == header  # Same section
        ):
            # Merge with previous chunk
            prev_header, prev_text = merged_chunks[-1]
            merged_chunks[-1] = (prev_header, prev_text + "\n\n" + chunk_text)
        else:
            merged_chunks.append((header, chunk_text))

    # Build final TextChunk objects
    chunks: list[TextChunk] = []
    current_offset = 0

    for header, chunk_text in merged_chunks:
        # Find the actual offset in the original text
        offset = text.find(chunk_text[:80], current_offset)
        if offset == -1:
            offset = current_offset

        token_count = count_tokens(chunk_text)

        chunk = TextChunk(
            chunk_id=f"{doc_id}__chunk_{len(chunks):04d}",
            doc_id=doc_id,
            text=chunk_text,
            start_offset=offset,
            end_offset=offset + len(chunk_text),
            token_count=token_count,
            section_header=header,
        )
        chunks.append(chunk)
        current_offset = offset + len(chunk_text)

    return chunks
