# Todo List

## Immediate

- [x] Install runtime dependencies from `requirements.txt` (venv recreated — old one was broken by the OneDrive move — deps installed via uv, 2026-09-01)
- [x] Verify the app imports cleanly in the current environment (`pytest tests -q` → 31 passed)
- [x] Start the backend and confirm the health endpoint works (`/health` OK on port 8001; port 8000 is taken by Docker/WSL on this machine)
- [x] Run a sample ingest flow on a known document (4 docs / 432 chunks already indexed from prior sessions; retrieval verified against them)
- [x] Run a basic query to validate retrieval and answer generation — **verified end-to-end with live generation + citations after the Gemini backend was added (2026-09-01)**

## Retrieval / quality

- [x] Inspect BM25 and vector hits for a sample query (both top-1 = correct FastAPI chunk)
- [x] Validate RRF fusion output and reranker ordering (fusion merges both sources; rerank scores 8.82/5.86/-0.48)
- [x] Check whether context compression preserves necessary evidence (3 spans, 320 chars kept for the test question)
- [x] Compare vector-only vs hybrid — **full 20-question RAGAS comparison captured 2026-09-01/02 (see README scorecard)**

## Evaluation

- [x] Run the default QA set through the evaluation harness (first full run 2026-09-01 — but results invalid, see below)
- [x] Confirm RAGAS metrics load successfully
- [x] Save at least one evaluation run to the database
- [x] Fix harness so failed generations are excluded from RAGAS scoring instead of scored as zero (2026-09-01)
- [x] Harden LLM retry policy for long eval runs (5 attempts, 2–30s backoff, fail fast on non-retryable 4xx) (2026-09-01)
- [x] Diagnose low context_recall: retrieval coverage fine (19/20), sentence-level compression destroyed evidence on 13/20 (2026-09-01)
- [x] Make compression budget-conditional (pass-through under `max_context_tokens`) (2026-09-01)
- [x] Add regression tests for the harness failure-exclusion and compressor budget behavior (2026-09-01, `tests/test_harness.py` + `tests/test_compressor.py`)
- [x] Handle provider quota exhaustion: gemini-3.5-flash is 20 req/day free tier; generation temporarily on flash-lite (see docs/progress.md) (2026-09-01)
- [x] Re-run the eval with all fixes — **hybrid complete and clean (2026-09-01, `eval_dc701f3b`): faithfulness 1.0, answer_relevancy 0.9502, context_precision 0.8571, context_recall 1.0, 0 failures; README scorecard populated**
- [x] Capture the vector-only baseline — **DONE 2026-09-02 (`eval_7c8461c4`): faithfulness 1.0, relevancy 0.897, precision 0.868, recall 0.947, 0 failures** — via a fresh-key Gemini project (quota is per project); README scorecard fully populated with deltas
- [x] Corpus dedupe executed (2026-09-02): duplicate gatsby copy removed (195 chunks), content hashes backfilled, stores verified clean, diagnostic re-run (16/20 full evidence)
- [x] Generator model decision: `gemini-3.5-flash` = 503 high-demand on free tier (even with a fresh key) → **flash-lite is permanent**; `.env` documents this
- [x] Final verification: 43/43 tests, backend `/health` OK (3 docs / 237 chunks), `/eval/runs` serves both clean scorecard arms, **live `/query` verified end-to-end** (answer + citations + retrieval debug on the deduped corpus, 2026-09-02)

## Retrieval / quality (new open items from the 2026-09-01 diagnosis)

- [ ] Q14 rerank miss (diagnosed, numbers recorded 2026-09-01): for "How do you profile Python code for performance?" ALL candidates score negative on the cross-encoder (−2.8 to −6.3) and the evidence chunk ranks #8 (−6.309) — a ranking failure of ms-marco-MiniLM on question-style queries, not a retrieval failure (pool coverage 1.00). Candidate fix: raise `rerank_top_n` 5→8 (evidence lands at rank 8; ~100 extra tokens, far under budget) — held at ~90% confidence because extra chunks may dilute RAGAS context_precision on the other 19 questions. Note: harness previously hardcoded top_n=5, ignoring the `rerank_top_n` config — fixed to read the config, so the experiment now only needs a `.env` change + eval re-run.
- [ ] Small chunking losses on 2 questions (pool coverage 0.89–0.93) — inspect chunk boundaries for the affected docs
- [ ] Cross-encoder upgrade experiment (e.g. bge-reranker-base) — Q14-style ranking failures are a known ms-marco-MiniLM weakness on question-form queries; needs a benchmarked A/B before switching

## Documentation / maintainability

- [x] Keep the architecture docs current with the live implementation (`docs/progress.md` updated with validation evidence, 2026-09-01)
- [x] Record any environment-specific constraints or provider limitations (port 8000 conflict; per-backend key status in docs/progress.md)
- [x] Note which features are validated versus still experimental
- [x] Fix stale `.env.example` (was missing Gemini backend + several settings) and incomplete `requirements.txt` (langchain judge stack missing) (2026-09-02)
- [x] Create `sample_docs/` referenced by the README; add ingestion duplicate guard + tests (43 passing) (2026-09-02)
- [x] Run `dedupe_corpus.py` after the vector-only eval — done 2026-09-02 (195 duplicate chunks removed; 3 docs / 237 chunks; hashes backfilled; stores verified)
- [x] Generator decision final: flash returns 503 high-demand even on a fresh key → flash-lite stays permanent (see docs/progress.md)

## Optional / stretch

- [ ] Add backend config monitoring for model provider health
- [ ] Add comparison dashboards for multiple eval runs
- [ ] Expand the QA set with project-specific scenarios
- [ ] Improve deployment packaging and environment automation

## Status note

The full stack is installed, tested (31/31), and validated end-to-end with live generation. The retrieval pipeline, generation with citations, and the RAGAS harness have all run. The remaining work is capturing a clean hybrid vs vector-only scorecard (re-run in progress) and the two retrieval-quality open items listed above.
