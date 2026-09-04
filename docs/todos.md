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
- [x] Git initialized on `main` with initial commit `875bbbe` (89 files); `.gitignore` extended (logs, `data/uploads/`, `.pytest_cache/`, local installer); README gained a repo-tooling-scripts section (2026-09-02)

## Retrieval / quality (new open items from the 2026-09-01 diagnosis)

- [ ] Q14 rerank miss (diagnosed, numbers recorded 2026-09-01): for "How do you profile Python code for performance?" ALL candidates score negative on the cross-encoder (−2.8 to −6.3) and the evidence chunk ranks #8 (−6.309) — a ranking failure of ms-marco-MiniLM on question-style queries, not a retrieval failure (pool coverage 1.00). Candidate fix: raise `rerank_top_n` 5→8 (evidence lands at rank 8; ~100 extra tokens, far under budget) — held at ~90% confidence because extra chunks may dilute RAGAS context_precision on the other 19 questions. Note: harness previously hardcoded top_n=5, ignoring the `rerank_top_n` config — fixed to read the config, so the experiment now only needs a `.env` change + eval re-run. Re-confirmed 2026-09-04 on the deduped corpus via `diagnose_retrieval.py` (needs `$env:PYTHONPATH` = repo root, see `scripts/archive/README.md`): pool=1.00 → rerank=0.08, still the only severe rerank loss (16/20 full survival).
- [ ] Small chunking losses on 2 questions (pool coverage 0.89–0.93) — inspect chunk boundaries for the affected docs. 2026-09-04 re-run suggests these may be stemming artifacts of the keyword-overlap heuristic, not real losses: Q7 misses only 'providing', Q13 only 'explain' (inflections of words present in the pool). Downgrade priority; confirm with stemmed overlap before touching the chunker.
- [ ] Cross-encoder upgrade experiment (e.g. bge-reranker-base) — Q14-style ranking failures are a known ms-marco-MiniLM weakness on question-form queries; needs a benchmarked A/B before switching

## Documentation / maintainability

- [x] Keep the architecture docs current with the live implementation (`docs/progress.md` updated with validation evidence, 2026-09-01)
- [x] Record any environment-specific constraints or provider limitations (port 8000 conflict; per-backend key status in docs/progress.md)
- [x] Note which features are validated versus still experimental
- [x] Fix stale `.env.example` (was missing Gemini backend + several settings) and incomplete `requirements.txt` (langchain judge stack missing) (2026-09-02)
- [x] Create `sample_docs/` referenced by the README; add ingestion duplicate guard + tests (43 passing) (2026-09-02)
- [x] Run `dedupe_corpus.py` after the vector-only eval — done 2026-09-02 (195 duplicate chunks removed; 3 docs / 237 chunks; hashes backfilled; stores verified)
- [x] Generator decision final: flash returns 503 high-demand even on a fresh key → flash-lite stays permanent (see docs/progress.md)
- [x] Groq fallback backend live (2026-09-02): key valid, model `openai/gpt-oss-120b` (old `llama-3.3-70b-versatile` decommissioned on Groq), `reasoning_effort=low` added (measured 7.6s → 0.6s per generation) — single-provider fragility resolved
- [x] GitHub Actions CI added (2026-09-02, `.github/workflows/ci.yml`): ruff (config in pyproject.toml), gitleaks secret scan, pytest incl. 5 new end-to-end API smoke tests (hermetic TestClient, real embeddings into isolated stores, duplicate guard, mocked-generation query pipeline) — keyless, 48/48 passing; repo lint-clean
- [x] Deployment decision recorded in docs/prod.md: AWS (Lightsail/EC2 t3.medium, 4 GB RAM) — Vercel rejected (no persistent disk for ChromaDB/BM25/SQLite, can't host Streamlit)

## Optional / stretch

- [ ] Add backend config monitoring for model provider health
- [ ] Add comparison dashboards for multiple eval runs
- [ ] Expand the QA set with project-specific scenarios
- [ ] Improve deployment packaging and environment automation

## Code quality review (2026-09-03)

- [x] Single-frontend decision: `ui/` deleted 2026-09-03 (disconnected, not in Docker image, fake demo data); `frontend/` Streamlit kept as interim
- [x] Vite scaffold removed with `ui/` (`src/`, `dist/`, `node_modules/`, package files all gone)
- [x] New frontend: `web/` scaffolded 2026-09-03 (Next 16 + React 19 + Tailwind v4, TS, ESLint clean, webpack prod build green) — routes `/`, `/ask`, `/ingest`, `/eval`, `/system`, `/topology` (Option 1: real retrieval path), typed `lib/api.ts`, `Dockerfile.web`; Streamlit stays until parity cutover
- [x] Dead symbols removed 2026-09-03: `QAEvalItem` (+docstring), `IngestRequest`, `build_prompt_with_metadata`, `get_embedding_dimension`, `bm25.get_chunk_count`, unused `db` param in `POST /query`, `sqlite_url` — 53/53 tests pass
- [x] Shared pipeline 2026-09-03: `app/retrieval/pipeline.py` serves `query.py` + `harness.py`; metadata lookup batched (was N+1); `tests/test_pipeline.py` locks wiring (model-backed paths still covered by smoke tests)
- [x] One-shot scripts archived 2026-09-03: `scripts/archive/` + README; `README.md` table repointed
- [x] `web/` in compose 2026-09-03: additive `web` service (`docker compose config` lists backend/streamlit/caddy/web); Caddy still on Streamlit until parity cutover
- [x] Env cleanup 2026-09-03: free-tier primaries only (gemini `flash-lite` + groq `gpt-oss-120b`); stale `LLM_PROVIDER`/`LLM_MODEL` removed from `.env`; `config.py` defaults + `.env.example` synced; ollama/cerebras/claude kept as opt-in code paths
- [x] Real-data endpoints 2026-09-03: `GET /documents` + `GET /config` (no secrets, covered by smoke tests) power `web/` System/Topology pages
- [x] Simplification WIP committed + pushed 2026-09-04 (`916a81c`; backup branch `backup-pre-simplify`; `web/.env.example` force-added — it holds only the public backend URL, no secrets): 53/53 tests via `.venv`, `ruff check` + `eslint` + `tsc --noEmit` clean
- [x] `web/` parity verified 2026-09-04 against live backend (fresh process; a stale 2026-09-02 backend was squatting on port 8001 and had to be killed — it served 404s for the new routes): `/health` (3 docs / 237 chunks / 8 eval runs), `/config`, `/documents`, `/eval/runs` all live; all 6 web routes (`/`, `/ask`, `/ingest`, `/eval`, `/system`, `/topology`) return 200 via `next dev --webpack` (Turbopack native binding still broken on this Windows box)
- [x] Caddy cutover DONE 2026-09-04: `web/lib/api.ts` uses relative `/api/*` when `NEXT_PUBLIC_BACKEND_URL` is unset (direct backend only in local dev); `next.config.ts` rewrite proxies `/api/*` for `npm run dev` (`BACKEND_INTERNAL_URL` override, needed as port 8000 is taken on this box); `deploy/Caddyfile` strips `/api` → `backend:8000`, everything else → `web:3000`; `streamlit` service retired from compose (code/image kept for rollback); `Dockerfile.web` bakes empty backend URL; `DEPLOY.md` updated. Verified: `tsc`+`eslint` clean, `docker compose config` lists backend/web/caddy, Caddyfile `caddy validate` green for both `:80` and domain (adapted JSON confirms strip+proxy), live `/api/health|config|documents|eval/runs` through `next dev --webpack` → backend `:8001`, `npm run build` (prod bake) green with all 7 routes static. Note: `caddy validate` needs `-e DOMAIN=...` in the container — without it even the old file fails (pre-existing quirk, not a regression).

## Status note (2026-09-04)

The full stack is installed, tested (53/53), and validated end-to-end with live generation. The clean hybrid vs vector-only scorecard is captured (README scorecard populated). The simplification batch is committed/pushed (`916a81c`) and `web/` parity is verified at route + contract + live-endpoint level. Remaining: (1) Caddy cutover design decision (blocked — see above), (2) retrieval experiments needing quota/time: `rerank_top_n` 5→8 eval re-run + bge-reranker A/B, (3) actual AWS provisioning per `DEPLOY.md` (runbook ready, not yet executed).
