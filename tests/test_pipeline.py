"""Shared retrieval pipeline: wiring + single batched metadata lookup.

All model-backed stages are monkeypatched, so this runs in milliseconds
with no embedding/reranker downloads. The model-backed paths are covered
by tests/test_api_smoke.py (real embeddings, real reranker, mocked LLM).
"""

from app.retrieval import bm25_index, vector_store
from app.retrieval import pipeline as pipeline_module
from app.retrieval.bm25_index import BM25SearchResult
from app.retrieval.compressor import CompressedChunk
from app.retrieval.reranker import RankedChunk
from app.retrieval.vector_store import VectorSearchResult


def _vec(cid: str) -> VectorSearchResult:
    return VectorSearchResult(chunk_id=cid, score=0.9, text=f"text-{cid}", metadata={})


def _compressed(cid: str) -> CompressedChunk:
    return CompressedChunk(
        chunk_id=cid,
        original_text=f"text-{cid}",
        compressed_text=f"text-{cid}",
        original_token_count=1,
        compressed_token_count=1,
        sentences_kept=1,
        sentences_total=1,
    )


def _install_fakes(monkeypatch, calls: list):
    monkeypatch.setattr(pipeline_module, "embed_query", lambda q: [0.1, 0.2])
    monkeypatch.setattr(
        vector_store, "search", lambda emb, top_k=20: [_vec("a"), _vec("b")]
    )
    monkeypatch.setattr(
        bm25_index,
        "search",
        lambda q, top_k=20: [BM25SearchResult(chunk_id="a", score=5.0, text="text-a")],
    )
    monkeypatch.setattr(
        pipeline_module,
        "rerank",
        lambda q, cands, top_n=5: [
            RankedChunk(chunk_id="a", score=1.0, text="text-a",
                        original_sources=["bm25", "vector"])
        ],
    )
    monkeypatch.setattr(
        pipeline_module, "compress_context", lambda q, chunks: [_compressed("a")]
    )

    def fake_get(ids: list[str]):
        calls.append(list(ids))
        return [
            VectorSearchResult(
                chunk_id=i, score=1.0, text=f"text-{i}",
                metadata={"doc_title": "T", "source_path": "P"},
            )
            for i in ids
        ]

    monkeypatch.setattr(vector_store, "get_chunks_by_ids", fake_get)


def test_hybrid_batches_metadata_lookup(monkeypatch):
    """One batched Chroma lookup (was one round-trip per chunk)."""
    calls: list = []
    _install_fakes(monkeypatch, calls)

    res = pipeline_module.run_retrieval_pipeline("q", mode="hybrid", top_n=5)

    assert calls == [["a"]]
    assert res.contexts == [("a", "text-a", "T", "P")]
    assert [r.chunk_id for r in res.vector_results] == ["a", "b"]
    assert [r.chunk_id for r in res.bm25_results] == ["a"]
    assert res.fused_results, "hybrid with BM25 hits must fuse"


def test_vector_only_skips_bm25(monkeypatch):
    """vector_only never touches the BM25 index and fuses nothing."""
    calls: list = []
    _install_fakes(monkeypatch, calls)
    bm25_called: list = []
    monkeypatch.setattr(
        bm25_index, "search",
        lambda q, top_k=20: bm25_called.append(q) or [],
    )

    res = pipeline_module.run_retrieval_pipeline("q", mode="vector_only", top_n=5)

    assert bm25_called == []
    assert res.fused_results == []
    assert res.contexts == [("a", "text-a", "T", "P")]


def test_empty_rerank_short_circuits(monkeypatch):
    """No candidates → empty result, no metadata lookup at all."""
    calls: list = []
    _install_fakes(monkeypatch, calls)
    monkeypatch.setattr(pipeline_module, "rerank", lambda q, cands, top_n=5: [])

    res = pipeline_module.run_retrieval_pipeline("q", mode="hybrid", top_n=5)

    assert res.reranked == [] and res.compressed == [] and res.contexts == []
    assert calls == []
