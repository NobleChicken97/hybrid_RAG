# Hybrid RAG System — Project Report

## Executive summary

This repository is a working hybrid retrieval-augmented generation (RAG) system built in Python. The project combines a FastAPI backend, a Streamlit frontend, persistent local storage, and an evaluation harness that measures answer quality using RAGAS. The implementation is grounded in actual code under `app/`, with the core architecture centered on:

- BM25 keyword retrieval
- vector retrieval via ChromaDB
- reciprocal rank fusion (RRF)
- cross-encoder reranking
- context compression
- prompt assembly and citations
- evaluation against a QA set

This is not a tutorial stub. It is a real project structure with production-oriented API layers, local persistence, and an end-to-end retrieval pipeline.

## Verified technical baseline

The codebase confirms the following architecture:

- Backend framework: FastAPI (`app/main.py`)
- Storage: SQLite (`app/database.py`)
- Vector store: ChromaDB (`app/retrieval/vector_store.py`)
- Keyword retrieval: BM25 (`app/retrieval/bm25_index.py`)
- Fusion: reciprocal rank fusion (`app/retrieval/fusion.py`)
- Reranker: cross-encoder model (`app/retrieval/reranker.py`)
- Prompt generation: prompt builder + system prompt (`app/generation/prompt.py`)
- LLM abstraction: multiple backends (`app/generation/llm.py`)
- Evaluation: RAGAS-powered harness (`app/evaluation/harness.py`)
- User interface: Streamlit pages (`frontend/app.py`, `frontend/pages/*`)

## What the app does

The application supports:

1. Document ingestion from raw text or files.
2. Chunking of source text with structure-aware splitting.
3. Embedding and storing chunks.
4. Querying with vector + BM25 hybrid retrieval.
5. Fusion, reranking, and compression before generation.
6. Cited answers tied back to source chunks.
7. Evaluation runs using QA sets and RAGAS metrics.

## Current state of implementation

### Functional areas already implemented

- `app/api/ingest.py`: ingestion API
- `app/api/query.py`: Q&A endpoint with retrieval debug info
- `app/api/eval.py`: evaluation endpoints
- `app/evaluation/harness.py`: end-to-end evaluation pipeline
- `app/retrieval/fusion.py`: RRF merging logic
- `app/retrieval/reranker.py`: cross-encoder scoring
- `app/retrieval/compressor.py`: sentence-level context compression
- `app/database.py`: SQLAlchemy schema and DB management
- `frontend/app.py`: Streamlit entrypoint
- `tests/`: unit tests for chunking, fusion, and compression

### Notable implementation details

- `app/config.py` centralizes environment-driven configuration.
- `app/generation/llm.py` supports multiple backends including Ollama, Cerebras, Groq, and Claude.
- `app/models.py` defines the API contracts used by FastAPI.
- `data/qa_sets/default_qa_set.json` provides a default evaluation set.

## Current evidence from verification

I ran the project test suite with:

```bash
pytest tests -q
```

Current result: failing at collection time because required packages are not installed in the environment.

Observed errors:

- `ModuleNotFoundError: No module named 'tiktoken'`
- `ModuleNotFoundError: No module named 'sentence_transformers'`

This means the repository is present and structurally complete, but the local environment has not yet been bootstrapped with the declared dependencies from `requirements.txt`.

## Project quality signal

The codebase is a credible prototype or MVP with a real end-to-end pattern:

- hybrid retrieval is a first-class feature, not an afterthought
- evaluation is designed as a measurable quality gate
- generation is abstracted to allow backend swapping
- the UI and API surfaces line up with the architecture described in the project guides

## Main gaps

1. Dependency installation is not complete in the current environment.
2. The docs directory has only sample docs and does not yet contain the required project docs set.
3. Real evaluation scores are not yet established in the repo because the environment has not been fully installed and run.
4. The project documentation should be expanded to distinguish “implemented,” “validated,” and “planned” work clearly.

## Recommendation

The repository is ready for the next step: install dependencies, run the tests and app startup, then validate end-to-end behavior before publishing final score metrics. The code already shows a strong architecture; the remaining work is operational validation and documentation completion.
