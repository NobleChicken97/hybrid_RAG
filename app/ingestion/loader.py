"""
Document loaders for PDF, Markdown, and plain text files.

Each loader extracts raw text while preserving structural markers
(headers, paragraphs) that the chunker needs for context-aware splitting.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RawDocument:
    """A loaded document before chunking."""
    text: str
    title: str
    source_path: str
    file_type: str  # 'pdf', 'md', 'txt'
    metadata: dict = field(default_factory=dict)


def load_pdf(path: str | Path) -> RawDocument:
    """
    Load a PDF document using pdfplumber.

    pdfplumber preserves layout better than pypdf for most documents.
    Falls back to pypdf if pdfplumber fails.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    try:
        import pdfplumber

        pages = []
        with pdfplumber.open(path) as pdf:
            for _i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    pages.append(text)

        full_text = "\n\n".join(pages)

    except Exception:
        # Fallback to pypdf
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        full_text = "\n\n".join(pages)

    return RawDocument(
        text=full_text.strip(),
        title=path.stem,
        source_path=str(path),
        file_type="pdf",
        metadata={"page_count": len(pages)},
    )


def load_markdown(path: str | Path) -> RawDocument:
    """
    Load a Markdown document, preserving header structure.

    Headers are kept as-is because the chunker uses them for
    context-aware splitting boundaries.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Markdown file not found: {path}")

    text = path.read_text(encoding="utf-8")

    # Count structure markers for metadata
    headers = re.findall(r"^#{1,6}\s+.+$", text, re.MULTILINE)

    return RawDocument(
        text=text.strip(),
        title=path.stem,
        source_path=str(path),
        file_type="md",
        metadata={"header_count": len(headers)},
    )


def load_text(path: str | Path) -> RawDocument:
    """Load a plain text document."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Text file not found: {path}")

    text = path.read_text(encoding="utf-8")

    return RawDocument(
        text=text.strip(),
        title=path.stem,
        source_path=str(path),
        file_type="txt",
        metadata={},
    )


def load_from_raw_text(raw_text: str, title: str) -> RawDocument:
    """Create a RawDocument from inline text (no file on disk)."""
    return RawDocument(
        text=raw_text.strip(),
        title=title,
        source_path="<inline>",
        file_type="txt",
        metadata={"source": "inline"},
    )


# ─── Dispatcher ──────────────────────────────────────────────────────────────

_LOADER_MAP = {
    ".pdf": load_pdf,
    ".md": load_markdown,
    ".markdown": load_markdown,
    ".txt": load_text,
    ".text": load_text,
    ".rst": load_text,  # Treat RST as plain text for now
}


def load_document(path: str | Path) -> RawDocument:
    """
    Load a document based on file extension.

    Supported: .pdf, .md, .markdown, .txt, .text, .rst
    """
    path = Path(path)
    ext = path.suffix.lower()

    loader = _LOADER_MAP.get(ext)
    if loader is None:
        raise ValueError(
            f"Unsupported file type: {ext!r}. "
            f"Supported: {', '.join(_LOADER_MAP.keys())}"
        )

    return loader(path)
