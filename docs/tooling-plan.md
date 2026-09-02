# Hybrid RAG Project — Skills and MCP Use Guide

This file is project-specific. Its purpose is to state which skills and MCP tools matter for this Hybrid RAG work, what each one should be used for, and what the actual workflow should look like without overcomplicating the stack.

The project is already well documented in the Markdown files under the docs folder. This file is the operational map: how to use the best available tooling for this exact scenario.

---

## 1. Project context

This project is a production-style retrieval-augmented generation system that combines:

- BM25 keyword retrieval
- vector retrieval using embeddings
- reciprocal rank fusion (RRF)
- reranking with a cross-encoder
- context compression before generation
- citations on every answer
- a held-out QA eval harness using RAGAS

The real value is not just building a chatbot over documents. The real value is proving that retrieval quality is measured, compared, and improved with objective metrics.

---

## 2. Best-fit MCP tools for this project

### 2.1 context7
Use for:
- FastAPI/Starlette API patterns
- ChromaDB integration details
- sentence-transformers / BGE model usage
- RAGAS metric usage and schema
- Anthropic API contract details when needed

Why it matters here:
- this project has many library contracts that change over time
- it is safer to pull current API docs than to rely on memory or stale examples

### 2.2 serena
Use for:
- reading and editing the actual project files precisely
- renaming symbols across retrieval and evaluation modules
- code navigation across the ingestion, retrieval, generation, and eval stacks
- consistent refactors when the pipeline changes

Why it matters here:
- the project has multiple layers with cross-references; precise symbol-level editing is essential

### 2.3 graphify
Use for:
- understanding the repo structure before changing architecture
- mapping document flow, chunk flow, retrieval pipeline, and evaluation logic
- identifying missing connections or duplicate logic

Why it matters here:
- this is a multi-stage system; a graph view of the pipeline is useful before refactoring

### 2.4 motion
Use for:
- frontend polish only, if the UI needs animation or transitions
- dashboard animation or interaction improvements, not core retrieval logic

Why it matters here:
- this project is mostly backend + retrieval + evaluation, so motion is optional and should not distract from the actual engineering work

---

## 3. Best-fit skills for this project

### 3.1 python-testing-patterns
Use for:
- unit tests around chunking, fusion, compressor logic
- regression checks for retrieval logic
- eval harness smoke tests

Why it matters here:
- retrieval pipelines are fragile; test the real behavior instead of only checking outputs by hand

### 3.2 debugging-strategies
Use for:
- failing retrieval comparisons
- mismatched citation output
- eval score regressions
- weird prompt/context behavior

Why it matters here:
- a RAG pipeline often fails in subtle ways; systematic debugging is worth more than guesswork

### 3.3 python-code-style
Use for:
- keeping the codebase readable and consistent
- documenting data structures and retrieval steps clearly
- reducing hidden quality debt in the API and eval layers

### 3.4 rag-implementation
Use for:
- architecture decisions around retrieval stages
- chunking and document indexing patterns
- memory and retrieval flow design
- evaluating whether hybrid retrieval is implemented correctly

### 3.5 llm-evaluation
Use for:
- scoring the pipeline with fidelity, relevance, and context metrics
- designing the evaluation harness and metric interpretation
- deciding whether a change is actually an improvement

### 3.6 python-observability
Use for:
- logging retrieval debug metadata
- tracing what the model actually saw
- understanding why a response was grounded or not grounded

### 3.7 frontend-design / impeccable / webapp-testing
Use for:
- the Streamlit or frontend surfaces
- making the ask/eval UI easier to understand
- verifying the user can upload docs, ask questions, and inspect citations

Why they matter:
- the interface should help prove retrieval quality, not hide it behind confusing screens

### 3.8 research / codebase-design / domain-modeling
Use for:
- clarifying the product story before implementation changes
- reviewing whether the project architecture matches the intended portfolio narrative
- cleaning up the project description and design rationale

---

## 4. How the tools should be used in this exact scenario

### Stage A — project framing and architecture review
Use:
- graphify
- research
- codebase-design
- domain-modeling

Goal:
- confirm the repo still matches the portfolio story: hybrid retrieval, metrics, citations, and eval harness

### Stage B — implementation work
Use:
- serena for precise code edits and symbol-level refactors
- context7 for current library API documentation
- python-testing-patterns for test design
- python-code-style for clean implementation

Goal:
- build the ingestion, retrieval, and generation stack without accidental architectural drift

### Stage C — debug and validation
Use:
- debugging-strategies
- python-observability
- llm-evaluation

Goal:
- verify retrieval quality improvements are real and not just subjective

### Stage D — UI and demo polish
Use:
- impeccable
- frontend-design
- webapp-testing

Goal:
- make the demo show citations and retrieval debug information clearly

---

## 5. Recommended workflow for this repo

1. Treat the docs in the docs folder as the canonical project narrative.
2. Keep the code aligned with that narrative.
3. Use context7 before writing API-heavy logic, especially for FastAPI, ChromaDB, and evaluation libraries.
4. Use serena for editing because the project spans multiple service layers.
5. Use graphify once before major refactors to understand the pipeline and ensure no missing connections.
6. Use python-testing-patterns to lock in retrieval and fusion behavior.
7. Use llm-evaluation to judge changes by numbers, not by feelings.
8. Use the UI tools only after the backend works reliably.

---

## 6. Step-by-step project todos

### Todo 1 — Confirm the canonical project story
- Verify the core project idea is present in the Markdown docs.
- Ensure the docs include: project purpose, retrieval architecture, eval model, success metrics, and deliverables.
- Confirm the docs are the source of truth, not the root TXT drafts.

### Todo 2 — Lock the system design
- Validate the ingestion pipeline design.
- Confirm the chunking strategy is context-aware rather than fixed-size.
- Verify the retrieval stage is hybrid and includes reranking.
- Confirm citations and evaluation are core product requirements, not optional extras.

### Todo 3 — Build the retrieval pipeline
- Create the document loader.
- Implement context-aware chunking.
- Embed chunks and index them.
- Add BM25 indexing.
- Fuse retrieval results.
- Add reranking.
- Add context compression.

### Todo 4 — Add generation and citation support
- Build the query pipeline to generate answers from retrieved context.
- Ensure each answer includes source citations.
- Include retrieval_debug metadata to help explain why an answer was chosen.

### Todo 5 — Build the evaluation harness
- Prepare a held-out QA set.
- Run baseline vector-only scores.
- Run hybrid+rerrank scores.
- Compare the scorecards.
- Treat regressions as real failures, not just minor fluctuations.

### Todo 6 — Build the frontend
- Add an ingest page.
- Add a question page with citations visible.
- Add an eval dashboard with before/after comparison.
- Keep the UI focused on evidence rather than decorative complexity.

### Todo 7 — Final verification
- Confirm all major ideas are preserved in Markdown docs.
- Remove duplicate plain-text project drafts.
- Check that the repo is left with a clear, coherent documentation set.

---

## 7. Final decision for this repo

For this project, the highest-value tool stack is:

- context7
- serena
- graphify
- python-testing-patterns
- debugging-strategies
- rag-implementation
- llm-evaluation
- python-observability
- impeccable
- webapp-testing

This is the best combination for a retrieval-heavy, eval-driven portfolio project because it supports the actual engineering loop: understand the system, implement it, test it, debug it, measure it, and present it clearly.

The key rule is simple: do not let tools distract from the project outcome. The outcome is a hybrid RAG system that proves better retrieval and better answer grounding with metrics.

