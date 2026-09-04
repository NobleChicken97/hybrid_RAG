"""
Embedding wrapper for BAAI/bge-small-en-v1.5.

BGE models require a query prefix for asymmetric retrieval:
  - Queries get prefixed with "Represent this sentence: "
  - Documents/chunks are embedded as-is

This module lazily loads the model (first call) and caches it for reuse.
"""

from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.config import get_settings


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    """Load and cache the embedding model (singleton)."""
    settings = get_settings()
    print(f"[Embedder] Loading model: {settings.embedding_model}")
    model = SentenceTransformer(settings.embedding_model)
    print(f"[Embedder] Model loaded. Dimension: {model.get_embedding_dimension()}")
    return model


# BGE-small uses this prefix for queries in asymmetric retrieval
_QUERY_PREFIX = "Represent this sentence: "


def embed_chunks(texts: list[str], batch_size: int = 64) -> list[list[float]]:
    """
    Embed a batch of document chunks.

    Chunks are embedded WITHOUT the query prefix (they are passages, not queries).

    Args:
        texts: List of chunk texts to embed.
        batch_size: Batch size for encoding (64 is good for CPU).

    Returns:
        List of embedding vectors (each a list of floats).
    """
    if not texts:
        return []

    model = _get_model()
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=len(texts) > 100,
        normalize_embeddings=True,  # BGE works best with normalized embeddings
    )
    return embeddings.tolist()


def embed_query(query: str) -> list[float]:
    """
    Embed a single query string.

    Queries get the BGE prefix for asymmetric retrieval.

    Args:
        query: The query text to embed.

    Returns:
        Embedding vector as a list of floats.
    """
    model = _get_model()
    prefixed = _QUERY_PREFIX + query
    embedding = model.encode(
        prefixed,
        normalize_embeddings=True,
    )
    return embedding.tolist()
