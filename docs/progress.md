# Progress Status

## Summary

The repository contains a substantial and mostly coherent implementation of a hybrid RAG system. The project has clear architectural intent, core APIs, retrieval logic, and evaluation routines already in place.

> **2026-09-01 environment validation update:** the runtime was fully repaired and validated in this environment. All unit tests pass, the backend boots and serves `/health`, and the entire retrieval stack (embeddings, ChromaDB, BM25, RRF fusion, cross-encoder reranking, context compression) was verified end-to-end with live data. The only remaining blocker is generation: every configured LLM backend is currently unusable (see Blockers).

## Work completed

### Environment (validated 2026-09-01)

- **Root cause of previous import failures found:** the `.venv` was created at the old OneDrive path (`...\OneDrive\Desktop\projects\...`) and the project was later moved out of OneDrive, leaving the venv's internal paths pointing at a location that no longer exists (`Lib\site-packages` was missing).
- venv recreated at the current path (Python 3.11.9) and all dependencies installed via `uv` from `requirements.txt` (torch 2.13.0, transformers 5.16.1, chromadb, ragas, streamlit, etc.).
- `pytest tests -q` → **31 passed**.
- Backend boots via uvicorn and `/health` returns `{"status": "ok", "documents_count": 4, "chunks_count": 432, "llm_backend": "groq"}`.
- Note: port 8000 is occupied on this machine by Docker/WSL (another project, "TrakPlus API"). Run the backend on an alternate port, e.g. `uvicorn app.main:app --port 8001`, or stop that container. The frontend supports a backend-URL override.

### Retrieval stack (validated with live data, question: "What is FastAPI built on top of?")

- vector search (BGE-small, ChromaDB, 432 chunks): top-1 = FastAPI overview chunk, score 0.797
- BM25 search: top-1 = same chunk, score 22.51
- RRF fusion: 8 merged candidates, top-1 retrieved by *both* methods
- cross-encoder rerank (ms-marco-MiniLM): top scores 8.82 / 5.86 / -0.48 — sensible ordering
- context compression: 3 spans kept, 320 chars total
- the full `/query` request path executes through compression and fails only inside the LLM call (external API issue, not pipeline logic)

### Architecture and scaffolding

- project structure created with backend, frontend, retrieval, ingestion, generation, and evaluation modules
- FastAPI app bootstraps and router registration are in place
- SQLite database layer and schema are present
- ChromaDB and BM25 retrieval systems are implemented

### Retrieval and generation

- BM25 search is implemented and verified
- vector search is implemented and verified
- RRF fusion logic is implemented and verified
- cross-encoder reranking is implemented and verified
- context compression is implemented and verified
- citations and prompt assembly are implemented
- multi-backend LLM generation abstraction exists (ollama_qwen3, ollama_phi4mini, cerebras, groq, claude)

### Evaluation

- QA item schema exists (20-question default QA set at `data/qa_sets/default_qa_set.json`)
- evaluation harness exists
- RAGAS integration is configured in the code
- default QA set is included
- evaluation runs can be saved in the database
- **not yet run end-to-end** — blocked on a working generation backend (RAGAS judging also needs one)

### Frontend

- Streamlit pages exist for ingest, ask, and evaluation flows
- health check and system configuration are integrated into the UI
- standalone `ui/` web app with configurable `BACKEND_URL_OVERRIDE`

### Testing

- 31 unit tests for chunking, fusion, and compression logic — **all passing**

## Current status

### Verified

- dependency installation, clean imports, full test suite
- backend startup and health endpoint
- entire retrieval pipeline with real indexed data (4 documents, 432 chunks)

### Not yet verified

- LLM answer generation + citations (blocked, see below)
- RAGAS evaluation scorecard (blocked on generation + judge backend)

## Current blockers

1. ~~**Generation backend unavailable**~~ — **RESOLVED 2026-09-01**: user supplied a free Gemini API key. A `gemini` backend was implemented in `app/generation/llm.py` (first-party OpenAI-compatible endpoint) and wired into `.env` (`LLM_BACKEND=gemini`, `GEMINI_MODEL=gemini-3.5-flash`, judge: `gemini-3.5-flash-lite`). End-to-end `/query` with live generation + citations verified.
2. ~~RAGAS judge blocked~~ — **RESOLVED**: judge wired to `gemini-3.5-flash-lite`.
3. Full 20-question RAGAS scorecard capture in progress.

### Fixes applied on 2026-09-01 (all verified by live runs)

- **venv rebuilt** at the current (post-OneDrive-move) path; deps installed via uv; 31/31 tests pass.
- **`app/config.py`**: added `gemini_api_key`, `gemini_model`, `gemini_base_url` settings.
- **`app/generation/llm.py`**: added `gemini` backend (`_get_gemini_client` + branch), with `timeout=90, max_retries=1` so hung requests fail fast and tenacity retries (free-tier latency spikes observed: 45s+ on some models).
- **`app/evaluation/harness.py`**: ragas 0.4 adaptation —
  - ragas >= 0.4 ignores the legacy `OPENAI_*` env vars (it called api.openai.com and got 401), so an explicit judge `LangchainLLMWrapper(ChatOpenAI(...))` is passed to `evaluate()`;
  - local HuggingFace embeddings (`BAAI/bge-small-en-v1.5`) are passed for `answer_relevancy` — deterministic, no extra cloud calls;
  - `bypass_n=True` on the wrapper: Gemini's OpenAI-compat endpoint rejects `n>1` ("Multiple candidates is not enabled"); bypass_n makes ragas send n separate requests;
  - `RunConfig(max_workers=4, timeout=600, max_wait=30)`: judge calls can exceed ragas's default timeout;
  - results handling supports ragas 0.4's `EvaluationDataset` (via `to_pandas()`, NaN-safe means) with a fallback for older dict-style results.
- **Model selection (measured latency on the free tier, 2026-09-01):** `gemini-3.5-flash` ≈ 1s, `gemini-3.5-flash-lite` ≈ 3s, `gemini-3.6-flash` ≈ 45s (throttled), `gemini-3.7-flash` = 503 high demand. Generation therefore uses `gemini-3.5-flash`.
- **Dependency alignment:** ragas 0.4.3 (latest) is incompatible with langchain-community 0.4.x (removed `chat_models.vertexai`); langchain stack pinned to 0.3.x (`langchain 0.3.x / core 0.3.x / community 0.3.x / openai 0.3.x`).

### Smoke-test eval results (2 QA items, hybrid mode) — run saved `eval_445af862`

- faithfulness 1.0, answer_relevancy 0.977, context_precision None→(timeout, since fixed), context_recall 0.5 (one item's ground truth not fully in compressed context — a real, useful signal)

## Next recommended action

Complete the full 20-question eval (hybrid + vector_only) and populate the README scorecard from `eval_results.json`.

## Full eval findings + fixes (2026-09-01, later session)

The first full 20-question eval (both modes) completed, but the results were **invalid as a comparison**:

- **vector_only baseline poisoned:** 14/20 questions failed generation with `CloudAPIError` (transient Gemini free-tier connection drops during the ~40-min run). The harness stored the literal error string (`"Error: RetryError[...]"`) as the answer with empty contexts, and RAGAS scored it as 0 → aggregate faithfulness 0.158 was an artifact, not a retrieval measurement. Archived as `eval_results_invalid_run_20260901.json`.
- **hybrid run degraded the same way:** 4/20 failures scored as 0, plus RAGAS judge-side `APIConnectionError`/`TimeoutError`s producing NaNs that skewed the means. Raw hybrid scores (faithfulness 0.7, answer_relevancy 0.6385, context_precision 0.5368, context_recall 0.4) were therefore *pessimistic*.

### Fixes applied (all verified, 31/31 tests pass)

1. **`app/evaluation/harness.py` — failed generations no longer scored.** Questions whose generation raises are excluded from the RAGAS dataset (scoring an error string is meaningless) but kept visible in the per-question breakdown with null scores, and a summary warning is printed. Empty-dataset edge case handled explicitly.
2. **`app/generation/llm.py` — retry hardening.** 5 attempts (was 3) with exponential backoff 2–30s (was 2–10s). New `NonRetryableCloudAPIError` subclass: 4xx responses other than 429 fail fast instead of burning retries.
3. **`app/evaluation/harness.py` — judge resilience.** RAGAS judge `ChatOpenAI` now gets `timeout=120, max_retries=3` so transient judge-side drops are absorbed by the SDK instead of becoming NaN rows.
4. **`app/retrieval/compressor.py` — budget-conditional compression.** Diagnosis (below) showed sentence-level compression destroys evidence; compression now passes context through intact when it fits `max_context_tokens` (2000) and only filters when over budget.

### Retrieval diagnosis (new script `diagnose_retrieval.py`, no LLM needed)

For all 20 QA questions, ground-truth keyword coverage was measured at three pipeline stages:

- **Retrieval pool (top-20 fused): evidence present for 19/20 questions** — the hybrid retrieval stage is not the bottleneck.
- **Compression destroyed evidence on 13/20** (e.g. "Starlette/Pydantic" for Q1 present after rerank, gone after compression).
- Threshold sweep (0.3 / 0.0 / −0.5 / −1.0 / −2.0) barely moved coverage (0.605 → 0.664) — the loss is inherent to sentence-level query-similarity filtering, because the sentence containing the answer often does not restate the query's keywords. Keeping everything (−99) recovered 0.939 coverage at ~180 tokens average vs a 2000-token budget — compression saved ~90 tokens for ~40% of the evidence. Hence fix #4.
- Remaining known loss: 1 rerank miss (Q14 "profile Python code" — cross-encoder ranks the cProfile chunk outside top-5) and small chunking losses (2 questions at pool 0.89–0.93). Open items, not fixed this session.

### Status

- **Hybrid: COMPLETE and clean** — run `eval_dc701f3b` (2026-09-01, generator + judge `gemini-3.5-flash-lite`): **faithfulness 1.0, answer_relevancy 0.9502, context_precision 0.8571, context_recall 1.0**, 0 failed generations, 1797s. README scorecard populated with these numbers.
- **Vector-only: pending quota.** The flash-lite daily quota was exhausted during its judging phase; all 20 vector_only generations 429'd. `eval_vector_only.py` (merge-only, quota-probe-guarded) was written and a one-shot scheduled run will capture the baseline after the midnight-Pacific reset (2026-09-02 ~12:48 IST). The context_recall 0.4 → **1.0** jump between the discarded run and the clean hybrid run directly validates the compression fix.

## Quota discovery + backend switch (2026-09-01, later session)

The first clean re-run was stopped after 0 successful generations: **`gemini-3.5-flash` free tier allows only 20 requests/day** (`GenerateRequestsPerDayPerProjectPerModel-FreeTier`), and the earlier eval runs had exhausted it. Backend live-test results:

| Backend | Result |
|---|---|
| gemini-3.5-flash | 429 — daily quota (20/day) exhausted |
| gemini-3.5-flash-lite | **OK** — separate, much larger daily quota bucket |
| gemini-3.6-flash | unusable (empty response) |
| cerebras gpt-oss-120b | 402 payment required |
| groq llama-3.3-70b-versatile | 401 invalid API key |
| ollama | not installed on this machine |
| anthropic | no key configured |

**Action taken:** generation temporarily switched to `gemini-3.5-flash-lite` (`.env` `GEMINI_MODEL`, with a TEMP comment to restore `gemini-3.5-flash` when quota resets — reset is daily, midnight Pacific). Same model for both eval modes keeps the hybrid vs vector-only comparison fair. End-to-end sanity check passed, and the compression fix is visibly working: the test answer now contains the full ground-truth detail ("Starlette for the web parts and Pydantic for the data parts") that the old compressor stripped.

**Also fixed:** eval config snapshot now records `generation_model` and `judge_model` (it previously recorded only backend names, which made historical runs ambiguous).

### Regression tests added (2026-09-01, later session)

- `tests/test_harness.py` (2 tests): failed generations are excluded from aggregate scores and stay visible with null scores; all-failed case skips RAGAS entirely. Locks in the fix for the poisoning bug.
- `tests/test_compressor.py` (+3 tests): under-budget pass-through without invoking the reranker; over-budget filtering engages; total token cap respected.
- Suite: **36 passed**. Note: ragas 0.4.3 emits deprecation warnings (`ragas.metrics` imports move to `ragas.metrics.collections` in v1.0) — future maintenance item, no action now.

## Project completion pass (2026-09-02, early session)

Repo-hygiene and correctness fixes found while closing out the project:

- **Duplicate corpus entry found and scheduled for removal:** `the-great-gatsby.pdf` was ingested twice on 2026-06-22 (`doc_c74bd5716030` + `doc_6974ad192700`, 195 chunks each — 432 total chunks included one full duplicate). New ingestion duplicate guard added: `Document.content_hash` (SHA-256 of extracted text) + a 409 response on re-ingest of identical content. SQLite migration is automatic and preserves eval history (`init_db` adds the column via `ALTER TABLE` when missing). `dedupe_corpus.py` removed the duplicate copy and backfilled hashes for the three surviving documents.
- **`requirements.txt` was incomplete:** the langchain stack needed by the RAGAS judge (`langchain 0.3.30 / core 0.3.86 / community 0.3.31 / openai 0.3.35`, plus `pandas`) was missing — a fresh install could not reproduce the eval. Added, pinned per the version-alignment notes in this file.
- **`.env.example` was stale:** missing the entire Gemini backend, `RAGAS_JUDGE_MODEL`, compression settings, and path settings. Rewritten to match `app/config.py`.
- **`sample_docs/` created** (README referenced it; it did not exist): `sample_fastapi.md`, `sample_python_guide.md`, `the-great-gatsby.pdf` — the three unique documents behind the indexed corpus.

## FINAL SCORECARD — project complete (2026-09-02)

The user supplied a fresh Gemini API key from a **new** Google project (free-tier quota is per project; the old bucket was exhausted), which unblocked the vector-only baseline immediately — no waiting for the midnight-Pacific reset. `gemini-3.5-flash` was also probed on the new key and returns **503 high-demand** (model availability, not quota), so **`gemini-3.5-flash-lite` is the permanent generation model** (`.env` documents this decision).

### Clean scorecard (both arms: generator + judge `gemini-3.5-flash-lite`, 0 failed generations, identical 432-chunk corpus)

| Metric | Vector-Only (`eval_7c8461c4`) | Hybrid + Rerank (`eval_dc701f3b`) | Delta |
|---|---|---|---|
| Faithfulness | 1.000 | 1.000 | +0.000 |
| Answer Relevancy | 0.897 | 0.950 | +0.053 |
| Context Precision | 0.868 | 0.857 | −0.011 |
| Context Recall | 0.947 | 1.000 | +0.053 |

Reading: hybrid wins answer relevancy and context recall (captures every ground-truth evidence span), matches faithfulness, and trades a small precision cost. With budget-conditional compression both arms are strong; the discarded run's huge asymmetry was an artifact of scoring API failures as answers.

### Post-scorecard corpus dedupe (verified)

- Removed `doc_6974ad192700` (duplicate gatsby copy): ChromaDB −195, BM25 −195, SQLite −1 doc → **3 documents, 237 chunks**.
- Verified: BM25 index has 0 stale IDs and gatsby queries hit only the surviving copy; vector count 237; `/health` OK; retrieval diagnostic on the deduped corpus: **16/20 questions keep full ground-truth evidence through all stages** (losses: 2 rerank, 2 chunking — no compression losses; pre-compression-fix baseline was 6/20).
- Note: the scorecard arms ran on the pre-dedupe 432-chunk corpus (deliberately, for arm comparability). The live demo corpus is now the clean 237-chunk one.

### Final state

- Test suite: **43 passed**. Backend verified via `/health` and `/eval/runs` (8 stored runs including both clean scorecard arms).
- Scorecard evidence: `eval_results.json` (merged), archived invalid run `eval_results_invalid_run_20260901.json`, full logs `full_eval3_*.log` / `vector_only_eval.log`.

## Evidence

## Evidence

Commands run and results (2026-09-01):

```bash
uv pip install --python .venv\Scripts\python.exe -r requirements.txt   # all deps installed
.venv\Scripts\python.exe -m pytest tests -q                            # 31 passed
uvicorn app.main:app --port 8001                                       # /health OK, 4 docs / 432 chunks
POST /query (hybrid)                                                   # 500 only at LLM call: Groq 401
# direct retrieval-stage script: all stages OK (see scores above)
```
