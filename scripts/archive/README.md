# Archived one-shot scripts

These completed their purpose during the 2026-09-01/02 validation and are
kept for provenance only. Run from the repo root if ever needed again
with the repo on the import path (they were written when they lived at the
root, so bare `python scripts/archive/...` fails with `ModuleNotFoundError`):
`$env:PYTHONPATH = (Get-Location).Path; python scripts/archive/diagnose_retrieval.py`.

| Script | Purpose | Status |
|---|---|---|
| `dedupe_corpus.py` | Removed the double-ingested gatsby PDF (195 chunks) + backfilled content hashes | Done 2026-09-02 |
| `diagnose_retrieval.py` | Traced ground-truth evidence through retrieval stages (no LLM calls); found the compression evidence loss | Done 2026-09-01 |
| `eval_full_run.py` | Ran the full 20-question QA set in both modes → `eval_results.json` | Done 2026-09-01 |
| `eval_vector_only.py` | Re-captured only the vector-only arm (quota-probe-guarded) | Done 2026-09-02 |
