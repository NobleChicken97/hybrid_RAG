"""
ChromaDB vector store wrapper.

Manages a single persistent collection for all document chunks.
Provides add, search, and delete operations.
"""

from dataclasses import dataclass

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import get_settings

_client = None
_collection = None

COLLECTION_NAME = "hybrid_rag_chunks"


@dataclass
class VectorSearchResult:
    """A single vector search result."""
    chunk_id: str
    score: float  # Distance (lower = more similar for cosine)
    text: str
    metadata: dict


def _get_client():
    """Get or create the ChromaDB persistent client."""
    global _client
    if _client is None:
        settings = get_settings()
        persist_dir = str(settings.chroma_db_abs_path)
        settings.chroma_db_abs_path.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        print(f"[VectorStore] ChromaDB client initialized at: {persist_dir}")
    return _client


def _get_collection():
    """Get or create the chunks collection."""
    global _collection
    if _collection is None:
        client = _get_client()
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},  # Use cosine similarity
        )
        print(f"[VectorStore] Collection '{COLLECTION_NAME}' ready. Count: {_collection.count()}")
    return _collection


def add_chunks(
    chunk_ids: list[str],
    embeddings: list[list[float]],
    documents: list[str],
    metadatas: list[dict] | None = None,
) -> None:
    """
    Add chunks to the vector store.

    Args:
        chunk_ids: Unique IDs for each chunk.
        embeddings: Embedding vectors for each chunk.
        documents: Raw text of each chunk.
        metadatas: Optional metadata dicts for each chunk.
    """
    collection = _get_collection()

    if metadatas is None:
        metadatas = [{}] * len(chunk_ids)

    # ChromaDB handles batching internally, but we batch for safety
    batch_size = 500
    for i in range(0, len(chunk_ids), batch_size):
        end = min(i + batch_size, len(chunk_ids))
        collection.add(
            ids=chunk_ids[i:end],
            embeddings=embeddings[i:end],
            documents=documents[i:end],
            metadatas=metadatas[i:end],
        )

    print(f"[VectorStore] Added {len(chunk_ids)} chunks. Total: {collection.count()}")


def search(query_embedding: list[float], top_k: int = 20) -> list[VectorSearchResult]:
    """
    Search the vector store for the most similar chunks.

    Args:
        query_embedding: The query embedding vector.
        top_k: Number of top results to return.

    Returns:
        List of VectorSearchResult sorted by similarity (best first).
    """
    collection = _get_collection()

    if collection.count() == 0:
        return []

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    search_results = []
    if results["ids"] and results["ids"][0]:
        for i, chunk_id in enumerate(results["ids"][0]):
            search_results.append(
                VectorSearchResult(
                    chunk_id=chunk_id,
                    score=1.0 - results["distances"][0][i],  # Convert distance to similarity
                    text=results["documents"][0][i],
                    metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                )
            )

    return search_results


def delete_document(doc_id: str) -> int:
    """
    Delete all chunks for a document from the vector store.

    Args:
        doc_id: The document ID whose chunks to delete.

    Returns:
        Number of chunks deleted.
    """
    collection = _get_collection()

    # Get all chunks for this document
    results = collection.get(
        where={"doc_id": doc_id},
        include=[],
    )

    if results["ids"]:
        collection.delete(ids=results["ids"])
        print(f"[VectorStore] Deleted {len(results['ids'])} chunks for doc_id={doc_id}")
        return len(results["ids"])

    return 0


def get_chunk_count() -> int:
    """Get the total number of chunks in the vector store."""
    collection = _get_collection()
    return collection.count()


def get_chunks_by_ids(chunk_ids: list[str]) -> list[VectorSearchResult]:
    """Retrieve specific chunks by their IDs."""
    collection = _get_collection()

    if not chunk_ids:
        return []

    results = collection.get(
        ids=chunk_ids,
        include=["documents", "metadatas"],
    )

    search_results = []
    if results["ids"]:
        for i, chunk_id in enumerate(results["ids"]):
            search_results.append(
                VectorSearchResult(
                    chunk_id=chunk_id,
                    score=1.0,
                    text=results["documents"][i] if results["documents"] else "",
                    metadata=results["metadatas"][i] if results["metadatas"] else {},
                )
            )

    return search_results
