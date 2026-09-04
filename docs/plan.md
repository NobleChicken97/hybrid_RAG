# Implementation / Execution Plan

## Objective

Move the Hybrid RAG System from a strong repository skeleton toward a validated, runnable, and documented project baseline.

## Phase 1 — Environment bootstrap

### Goal

Prepare a working Python environment for the project.

### Tasks

- install project dependencies from `requirements.txt`
- verify that `tiktoken`, `sentence_transformers`, `chromadb`, and other key libraries resolve
- ensure local model or cloud keys are configured according to backend needs

### Exit criteria

- `pytest` can run far enough to identify application-level issues rather than import failures
- backend modules import cleanly

## Phase 2 — Runtime validation

### Goal

Verify that the app boots and the main services run.

### Tasks

- run the FastAPI app startup
- confirm DB tables initialize correctly
- verify health endpoint behavior
- run ingest and query flows against a sample document

### Exit criteria

- app starts without runtime import errors
- sample document can be ingested
- a basic query returns an answer with citations or at least a retrieval pipeline response

## Phase 3 — Retrieval quality hardening

### Goal

Ensure the hybrid pipeline behaves consistently and returns meaningful context.

### Tasks

- validate chunk boundaries and section-aware splitting
- inspect BM25 and vector search outputs for a known query
- compare hybrid vs vector-only retrieval
- check reranker ordering and context compression behavior

### Exit criteria

- retrieved chunks are relevant and explainable
- top candidates are stable across similar questions
- compression does not destroy required evidence

## Phase 4 — Evaluation and measurement

### Goal

Turn the project into a measured system rather than a demo-only product.

### Tasks

- load default QA set
- run the evaluation harness with a known backend
- capture aggregate RAGAS metrics
- compare runs to understand performance deltas

### Exit criteria

- at least one eval run completes successfully
- a scorecard exists in the database or output stream
- results are meaningful enough to guide future tuning

## Phase 5 — Documentation and handoff

### Goal

Capture the exact state of the repo for future work.

### Tasks

- maintain architecture docs in `docs/`
- document verified status and gaps
- record runtime constraints and dependency expectations
- summarize the test and validation status with evidence

### Exit criteria

- the project has a durable knowledge base for continued work
- future contributors can see what is implemented, validated, and pending

## Risks and mitigations

### Risk: dependency issues

Mitigation: install the declared requirements before runtime testing.

### Risk: model access issues

Mitigation: use config-driven backends and test with a local or known-good provider path.

### Risk: evaluation is not yet grounded

Mitigation: use held-out QA data and keep a consistent evaluation method.

### Risk: context loss from compression

Mitigation: inspect compressed chunks and debug retrieval outputs before trusting answer quality.

## Planned final outcome

The project should end in a clean, repeatable baseline: dependencies installed, app running, evaluation harness working, and architecture docs kept current.

## Phase 6 — Codebase simplification (in progress 2026-09-03)

Goal: remove dead code and consolidate duplicated retrieval/frontend logic per the 2026-09-03 quality review (see todos.md).

- Done: `ui/` deleted (verified zero `.py` refs, not in `deploy/Dockerfile`; backend import + ruff still clean).
- Done 2026-09-03: env cleanup (gemini flash-lite + groq gpt-oss-120b free primaries; stale keys removed; defaults synced).
- Done 2026-09-03: `web/` scaffolded (Next 16 + React 19 + Tailwind v4; 6 routes with real backend data; `GET /documents` + `GET /config` added with smoke tests; `npm run lint` clean; `next build --webpack` green — Turbopack native binding broken on this Windows box, Dockerfile.web builds on linux where it works).
- Done 2026-09-03: shared `app/retrieval/pipeline.py` (query + harness converge; N+1 → single batched lookup; 53/53 tests), dead-symbol sweep, one-shot archive (`scripts/archive/`), `web/` compose service (additive; Caddy cutover pending parity check).
- Done 2026-09-04: Caddy cut over to `web/` via same-origin `/api/*` route (verified: caddy validate, live proxy chain, prod build). Retrieval RAGAS experiments DONE (top-8 + bge A/B, both clean); reranker-default decision pending. Remaining: AWS provisioning per `DEPLOY.md`.
