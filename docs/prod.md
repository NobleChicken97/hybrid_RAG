# Product Requirements / Product Definition

## Product summary

The Hybrid RAG System is a local-first document Q&A and evaluation application for knowledge work. It ingests documents, retrieves relevant context using multiple retrieval methods, answers questions grounded in source text, and reports evaluation metrics so improvements can be measured instead of guessed.

## Target user

This project is aimed at:

- developers learning RAG architecture
- technical builders validating retrieval quality
- demo users exploring document-grounded Q&A
- evaluation-driven AI practitioners comparing pipelines

## Core user needs

1. Upload or paste document content.
2. Retrieve relevant passages efficiently.
3. Ask a grounded question and receive an answer with citations.
4. Inspect retrieval internals to understand why the answer was chosen.
5. Run QA evaluation against a labeled set and compare model/pipeline behavior.

## Product goals

### Primary goals

- deliver accurate, citation-backed answers from uploaded documents
- combine BM25 and vector retrieval rather than relying on a single method
- provide measurable quality via RAGAS evaluation
- keep the system local and easy to run on a developer machine

### Secondary goals

- support multiple LLM backends without changing business logic
- maintain an interface that is easy for demos and experiments
- expose retrieval debug output so users can understand the pipeline

## Non-goals

- multi-tenant authentication or user accounts
- multi-modal document processing beyond text-like formats
- conversational memory across sessions
- large-scale production deployment as a managed service

## Functional requirements

### Ingestion

- Accept raw text or files such as `.md`, `.txt`, `.pdf`.
- Preserve document structure when chunking.
- Create chunks with metadata for document source and offsets.
- Store chunk embeddings and text in the local vector store.

### Querying

- Accept a natural-language question.
- Search both keyword and semantic stores.
- Fuse results with RRF.
- Rerank candidates using a cross-encoder.
- Compress context to the relevant portions.
- Generate a final answer with citations.

### Evaluation

- Run a pipeline over a QA set.
- Capture answer, context, and ground-truth comparisons.
- Produce RAGAS metrics including faithfulness, answer relevancy, context precision, and context recall.
- Save runs to a database for comparison.

### UX

- Provide a simple Streamlit interface for ingest, ask, and eval.
- Show health and backend status from the system UI.
- Expose debugging details in the ask flow.

## Quality bars

The project should not be considered successful unless:

- answers are supported by retrieved context
- citations can be traced to source chunks
- retrieval improvements are empirically measured
- evaluation runs are repeatable with a fixed QA set

## MVP definition

The MVP includes:

- ingestion pipeline
- hybrid retrieval pipeline
- queries with citations
- eval harness with measurement
- working local UI

## Deployment decision (2026-09-02): AWS, not Vercel

The system's storage is **local-persistent by design** (ChromaDB directory, BM25 pickle, SQLite file) and it loads ~200 MB of local models (BGE embeddings, ms-marco cross-encoder) into process memory.

- **Vercel is a poor fit**: serverless functions have no persistent disk (all three stores break), can't hold loaded models between invocations, and Streamlit is a long-lived websocket process Vercel doesn't host. Choosing Vercel would mean rearchitecting to managed vector DBs + API embeddings — which would erase the project's "runs on CPU, zero-infra" design point.
- **AWS (recommended)**: a single small instance preserves the architecture as-is. Options in order of simplicity:
  1. **Lightsail** (4 GB RAM plan, ~$24/mo, flat rate) — simplest; Docker or systemd.
  2. **EC2 t3.medium** (4 GB RAM, spot-able) — uses credits, full control; run both services via `docker compose` or the existing `run.py` behind Caddy/nginx with HTTPS.
  3. **ECS/Fargate** — only if container orchestration is the learning goal; overkill for a two-process demo.
- Minimum spec: 4 GB RAM (models + ChromaDB in memory), 20 GB disk (models + corpus), ports 8000/8501 behind a reverse proxy.

## Stretch items

- semantic caching
- incremental re-indexing
- query rewriting
- richer deployment packaging
- live model comparison across backends

## Product risk assessment

### Risks

- missing dependencies can block runtime validation
- model providers may have rate limits or unsupported models
- retrieval quality depends heavily on the QA set and chunking strategy
- context compression can accidentally remove critical evidence if thresholding is poor

### Mitigations

- use configuration-driven model selection
- keep local fallbacks available
- preserve retrieval debug output for diagnosis
- evaluate with held-out QA data, not just spot checks

## Product verdict

This project is best described as a technical demonstrator and learning prototype that targets the exact engineering discipline behind production-grade RAG systems: retrieval quality, evaluation, and grounded generation.
