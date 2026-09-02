"""
BM25 keyword search index using rank_bm25.

Runs alongside the vector store on the same chunk set.
Persists to disk via pickle so we don't rebuild on every restart.
"""

import pickle
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi

from app.config import get_settings


@dataclass
class BM25SearchResult:
    """A single BM25 search result."""
    chunk_id: str
    score: float
    text: str


# Module-level state
_bm25_index: BM25Okapi | None = None
_chunk_ids: list[str] = []
_chunk_texts: list[str] = []


def _tokenize(text: str) -> list[str]:
    """
    Simple tokenizer for BM25: lowercase, split on non-alphanumeric.

    Good enough at this corpus scale. No stemming/lemmatization needed.
    """
    return re.findall(r"\w+", text.lower())


def _get_index_path() -> Path:
    """Get the path to the persisted BM25 index."""
    settings = get_settings()
    settings.bm25_index_abs_path.mkdir(parents=True, exist_ok=True)
    return settings.bm25_index_abs_path / "bm25_index.pkl"


def build_index(chunk_ids: list[str], chunk_texts: list[str]) -> None:
    """
    Build a BM25 index from chunk texts.

    This replaces any existing index. Call after ingestion.

    Args:
        chunk_ids: Ordered list of chunk IDs (parallel with chunk_texts).
        chunk_texts: Ordered list of chunk texts to index.
    """
    global _bm25_index, _chunk_ids, _chunk_texts

    if not chunk_texts:
        print("[BM25] No chunks to index.")
        return

    # Tokenize all chunks
    tokenized = [_tokenize(text) for text in chunk_texts]

    # Build BM25 index
    _bm25_index = BM25Okapi(tokenized)
    _chunk_ids = list(chunk_ids)
    _chunk_texts = list(chunk_texts)

    # Persist to disk
    _save_index()
    print(f"[BM25] Index built with {len(chunk_ids)} chunks.")


def add_to_index(new_chunk_ids: list[str], new_chunk_texts: list[str]) -> None:
    """
    Add new chunks to the existing BM25 index.

    Since rank_bm25 doesn't support incremental adds, we rebuild
    with the full set. This is fine at our corpus scale (hundreds of chunks).
    """
    global _chunk_ids, _chunk_texts

    _ensure_loaded()

    _chunk_ids.extend(new_chunk_ids)
    _chunk_texts.extend(new_chunk_texts)

    build_index(_chunk_ids, _chunk_texts)


def search(query: str, top_k: int = 20) -> list[BM25SearchResult]:
    """
    Search the BM25 index for the most relevant chunks.

    Args:
        query: The search query.
        top_k: Number of top results to return.

    Returns:
        List of BM25SearchResult sorted by BM25 score (best first).
    """
    _ensure_loaded()

    if _bm25_index is None or not _chunk_ids:
        return []

    tokenized_query = _tokenize(query)
    if not tokenized_query:
        return []

    scores = _bm25_index.get_scores(tokenized_query)

    # Get top-k indices by score
    top_indices = np.argsort(scores)[::-1][:top_k]

    results = []
    for idx in top_indices:
        if scores[idx] > 0:  # Only include chunks with non-zero relevance
            results.append(
                BM25SearchResult(
                    chunk_id=_chunk_ids[idx],
                    score=float(scores[idx]),
                    text=_chunk_texts[idx],
                )
            )

    return results


def remove_document(doc_id: str) -> None:
    """Remove all chunks for a document and rebuild the index."""
    global _chunk_ids, _chunk_texts

    _ensure_loaded()

    # Filter out chunks belonging to this document
    filtered = [
        (cid, text)
        for cid, text in zip(_chunk_ids, _chunk_texts, strict=True)
        if not cid.startswith(doc_id + "__")
    ]

    if filtered:
        new_ids, new_texts = zip(*filtered, strict=True)
        build_index(list(new_ids), list(new_texts))
    else:
        _chunk_ids = []
        _chunk_texts = []
        _bm25_index = None
        _save_index()


def get_chunk_count() -> int:
    """Get the total number of indexed chunks."""
    _ensure_loaded()
    return len(_chunk_ids)


# ─── Persistence ─────────────────────────────────────────────────────────────

def _save_index() -> None:
    """Persist the BM25 index to disk."""
    path = _get_index_path()
    data = {
        "bm25_index": _bm25_index,
        "chunk_ids": _chunk_ids,
        "chunk_texts": _chunk_texts,
    }
    with open(path, "wb") as f:
        pickle.dump(data, f)
    print(f"[BM25] Index saved to {path}")


def _load_index() -> bool:
    """Load the BM25 index from disk. Returns True if loaded."""
    global _bm25_index, _chunk_ids, _chunk_texts

    path = _get_index_path()
    if not path.exists():
        return False

    try:
        with open(path, "rb") as f:
            data = pickle.load(f)
        _bm25_index = data["bm25_index"]
        _chunk_ids = data["chunk_ids"]
        _chunk_texts = data["chunk_texts"]
        print(f"[BM25] Index loaded from disk. {len(_chunk_ids)} chunks.")
        return True
    except Exception as e:
        print(f"[BM25] Failed to load index: {e}")
        return False


def _ensure_loaded() -> None:
    """Ensure the index is loaded (from disk if needed)."""
    global _bm25_index
    if _bm25_index is None:
        _load_index()
