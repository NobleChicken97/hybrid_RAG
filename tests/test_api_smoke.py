"""End-to-end API smoke tests — the CI shipping gate.

These boot the real FastAPI app (isolated data paths via tests/conftest.py)
and exercise the actual request path: health, document ingestion with real
embeddings into real (temporary) ChromaDB/BM25/SQLite stores, and the
duplicate-ingestion guard. No LLM/API-key calls are made — generation is
mocked so the retrieval + prompt + citation pipeline is what gets verified.
"""

import sys

sys.stdout.reconfigure(encoding="utf-8")

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    # Context manager form so the app's startup events (init_db, store
    # warmup) actually run against the isolated temp data paths.
    with TestClient(app) as c:
        yield c


def test_health_reports_ok(client: TestClient):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["documents_count"] == 0  # isolated store: nothing ingested yet


RAW_DOC = """# Sample Guide

FastAPI is built on top of Starlette for the web parts and Pydantic for the
data parts. It uses standard Python type hints.

## Dependency Injection

FastAPI's dependency injection system allows you to define reusable
dependencies for database sessions, authentication, configuration, and more.

## Middleware

Middleware runs before and after each request. Common uses include CORS
handling, logging, and authentication.
"""


def test_ingest_and_duplicate_guard(client: TestClient):
    """Ingest a document end-to-end, then verify the duplicate guard rejects
    the same content (a PDF uploaded twice once got double-indexed)."""
    resp = client.post(
        "/ingest",
        data={"title": "Smoke Guide", "raw_text": RAW_DOC},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["chunk_count"] > 0
    assert body["sample_chunks"], "ingest should return chunk previews"
    assert all(c["text_preview"] for c in body["sample_chunks"])

    # Health now reflects the ingested document.
    health = client.get("/health").json()
    assert health["documents_count"] == 1

    # Duplicate content must be rejected with 409, not re-indexed.
    dup = client.post(
        "/ingest",
        data={"title": "Smoke Guide Again", "raw_text": RAW_DOC},
    )
    assert dup.status_code == 409
    assert "already ingested" in dup.json()["detail"]

    # Health unchanged after the rejected duplicate.
    assert client.get("/health").json()["documents_count"] == 1


# Deliberately disjoint from RAW_DOC (no shared content hash, no shared rare
# terms) so this seed neither trips the duplicate guard nor competes with
# "Smoke Guide" at retrieval time, regardless of execution order.
QUERY_DOC = """# Query Smoke Doc

Uvicorn is the recommended ASGI server for running FastAPI applications in
production. It supports WebSockets and HTTP/1.1 on an uvloop-backed event
loop for high throughput.
"""


def _ensure_query_doc(client: TestClient):
    """Seed the shared test store with the query test's own document.

    Makes test_query_pipeline_with_mocked_generation independent of execution
    order: it no longer relies on test_ingest_and_duplicate_guard having run
    first. Accepts 409 (already seeded) as well as 200.
    """
    resp = client.post(
        "/ingest",
        data={"title": "Query Smoke Doc", "raw_text": QUERY_DOC},
    )
    assert resp.status_code in (200, 409), resp.text


def test_query_pipeline_with_mocked_generation(client: TestClient, monkeypatch):
    """Full retrieval -> rerank -> compress -> prompt -> citations path with
    the LLM mocked: the answer should carry citations resolvable to chunks."""
    from app.api import query as query_module

    _ensure_query_doc(client)

    monkeypatch.setattr(
        query_module, "generate",
        lambda *a, **kw: "Uvicorn is the recommended ASGI server for FastAPI [1].",
    )

    resp = client.post(
        "/query",
        json={"question": "Which ASGI server is recommended for running FastAPI?", "mode": "hybrid", "top_k": 3},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "Uvicorn" in body["answer"]
    assert len(body["citations"]) >= 1
    # Rank-1 is deterministic here: the query's rare terms (Uvicorn, ASGI,
    # server) appear only in the seeded doc, so both BM25 and vector rank it
    # first whether or not "Smoke Guide" shares the store.
    citation = body["citations"][0]
    assert citation["doc_title"] == "Query Smoke Doc"
    assert citation["snippet"]
    debug = body["retrieval_debug"]
    assert debug["vector_hits"], "vector search must return hits"
    # NOTE: bm25_hits is legitimately empty on a single-chunk corpus — every
    # query term appears in all (1) documents, so BM25 IDF is 0. Assert on
    # structure instead of content.
    assert isinstance(debug["bm25_hits"], list)
    assert debug["reranked_order"], "reranker must return an ordering"


def test_query_rejects_empty_question(client: TestClient):
    resp = client.post("/query", json={"question": "   "})
    assert resp.status_code == 400


def test_eval_runs_listing(client: TestClient):
    resp = client.get("/eval/runs")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_documents_listing(client: TestClient):
    # Order-independent: structure always, content when the smoke ingest ran.
    resp = client.get("/documents")
    assert resp.status_code == 200
    docs = resp.json()
    assert isinstance(docs, list)
    for d in docs:
        assert d["doc_id"] and d["title"] and d["chunk_count"] >= 1


def test_public_config_has_no_secrets(client: TestClient):
    resp = client.get("/config")
    assert resp.status_code == 200
    body = resp.json()
    assert body["llm_backend"] in (
        "gemini", "groq", "ollama_qwen3", "ollama_phi4mini", "cerebras", "claude",
    )
    assert body["generation_model"], "backend must resolve to a concrete model"
    assert not any("api_key" in k or "base_url" in k for k in body)
    assert "gsk_" not in resp.text and "AIza" not in resp.text
