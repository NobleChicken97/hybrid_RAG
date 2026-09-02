# Design Document

## Overview

The Hybrid RAG System is designed around a modular retrieval pipeline whose purpose is to maximize answer grounding and quality while staying small enough to run on a local developer environment. The core design principle is simple: retrieval quality should be measured and optimized intentionally, not left to chance.

## System architecture

```text
Documents
  -> Loader
  -> Chunker
  -> Embeddings
  -> ChromaDB
  -> BM25 index

Query
  -> Embed query
  -> Vector search + BM25 search
  -> Reciprocal rank fusion
  -> Cross-encoder rerank
  -> Context compression
  -> Prompt assembly
  -> LLM generation
  -> Answer + citations

Evaluation
  -> QA data set
  -> Full pipeline run
  -> RAGAS metrics
  -> Scorecard and comparison
```

## Layered design

### 1. Ingestion layer

Responsibilities:

- load `.pdf`, `.md`, `.txt`, and similar text inputs
- preserve semantic structure such as sections and headers
- split documents into chunks that balance semantic coherence and size

Implementation files:

- `app/ingestion/loader.py`
- `app/ingestion/chunker.py`

### 2. Embedding and retrieval layer

Responsibilities:

- convert chunks and queries to embedding vectors
- persist vectors in ChromaDB
- maintain a BM25 index for lexical relevance
- merge retrieval candidates using RRF
- rerank using a cross-encoder

Implementation files:

- `app/ingestion/embedder.py`
- `app/retrieval/vector_store.py`
- `app/retrieval/bm25_index.py`
- `app/retrieval/fusion.py`
- `app/retrieval/reranker.py`

### 3. Generation layer

Responsibilities:

- build the prompt from compressed context
- choose one of several backends for generation
- produce answer text grounded in the retrieval results
- attach citation metadata

Implementation files:

- `app/generation/prompt.py`
- `app/generation/llm.py`
- `app/generation/citations.py`

### 4. Evaluation layer

Responsibilities:

- load held-out QA pairs
- run end-to-end retrieval and generation for each question
- score answer quality with RAGAS metrics
- persist aggregate and per-question results

Implementation files:

- `app/evaluation/qa_loader.py`
- `app/evaluation/harness.py`
- `app/evaluation/scorecard.py`

### 5. Storage and metadata layer

Responsibilities:

- persist document metadata
- persist chunk metadata and section headers
- save eval runs and scorecards

Implementation files:

- `app/database.py`
- `app/models.py`

### 6. Interface layer

Responsibilities:

- provide simple user flows for ingestion, asking, and evaluation
- allow debugging of retrieval and model behavior

Implementation files:

- `frontend/app.py`
- `frontend/pages/1_Ingest.py`
- `frontend/pages/2_Ask.py`
- `frontend/pages/3_Eval.py`

## Design decisions

### Hybrid retrieval

The system intentionally combines semantic and lexical retrieval. This is the major product and technical advantage of the project.

- Vector retrieval catches semantic similarity.
- BM25 catches exact terminology and lexical matches.
- RRF combines them without needing perfectly calibrated scores.

### Cross-encoder reranking

The reranker re-scores only the top candidate set after fusion. This protects cost and latency while improving precision.

### Context compression

Compression is **budget-conditional**: when the retrieved context fits `max_context_tokens`, it is passed to the model intact; sentence-level trimming only engages when the context exceeds the budget.

Rationale (measured 2026-09-01): unconditional sentence-level filtering destroyed ground-truth evidence on 13/20 eval questions — the sentence containing the answer often does not restate the query's keywords, so a query-similarity filter drops it regardless of threshold. With top-5 reranked chunks averaging ~180 tokens against a 2000-token budget, the filter saved ~90 tokens at the cost of ~40% of the evidence. Under budget, pass-through is strictly better; over budget, the token cap still forces trimming.

### Citation grounding

Answers are tied back to chunk IDs and document metadata instead of being treated as free-form generative output. This is essential in a retrieval-driven system.

### Multi-backend model abstraction

The generation stack is designed to support future model providers without rewiring business logic. The model selection is environment-driven and abstracted behind a single `generate(...)` boundary.

## Data model summary

The codebase uses:

- `Document` for source metadata
- `Chunk` for chunk text and offsets
- `QAEvalItem` for QA pairs
- `EvalRun` for scores and config snapshots

This allows the system to be evaluated reproducibly over time.

## Operational concerns

### Local-first deployment

The project intentionally favors local persistence and CPU-friendly models. This keeps it approachable for developer work and demonstrations.

### Rate-limit handling

Cloud generation and judge flows are designed to fail clearly when keys or model access are missing. This matches the project’s instructions around backend fallback and model availability.

### Environment assumptions

The system expects environment configuration to exist through `.env` files and configuration values in `app/config.py`.

## Design quality assessment

The design aligns with common production RAG patterns:

- retrieval stage is explicitly optimized
- generation is grounded and constrained by context
- evaluation is not bolted on after the fact
- UI and API are simple but relevant

## Design gaps to watch

- model availability is a real operational risk in cloud backends
- production-grade security and auth were not the focus of this MVP
- some code paths may require explicit dependency bootstrapping before runtime

## Final assessment

This is a strong architecture for a local research or demo-grade hybrid RAG project. The design is coherent, modular, and evaluation-aware, which is exactly what makes it valuable as a technical portfolio project.
