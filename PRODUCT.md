# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary: the developer-owner, operating the system (ingesting documents, asking questions, running evals) from both local dev and the deployed site. Secondary: portfolio reviewers judging whether the RAG claims hold up — they click through live routes backed by a real backend, not a mock.

## Product Purpose

Operate a hybrid-retrieval RAG pipeline and prove it works with numbers: ingest documents, get cited answers with full retrieval debug, and score the pipeline with RAGAS — all against live data.

## Positioning

An evidence-first RAG console: every cited chunk and every score traces to a real retrieval path (BM25 + vector → RRF → bge-reranker → compression) that the UI exposes rather than hides. A neighboring demo cannot truthfully copy the per-chunk debug or the saved eval scorecards.

## Operating Context

Local dev: Next.js (`web/`, `npm run dev`) + FastAPI backend on :8000 (port taken by Docker/WSL on the dev machine — backend runs :8001 locally, rewrite proxies /api). Production: https://rag.noblechicken.me via Caddy (same-origin /api). Six routes: /, /ask, /ingest, /eval, /system, /topology. Evals are token-gated in prod (EVAL_TOKEN) and take 10–20 min; pushes to main auto-deploy via CD — never push mid-eval.

## Capabilities and Constraints

Six routes with fixed data contracts (`web/lib/api.ts` mirrors the FastAPI schemas — do not change shapes in a design pass). Stack is shadcn v4 + Tailwind v4 + Next 16. UI stays dark. No backend changes during visual work. Accessibility floor already established: visible focus, reduced-motion respected, body text contrast ≥ 4.5:1.

## Brand Commitments

Name: "Hybrid RAG / Retrieval Lab". Sharp-cornered geometry preferred (volunteered, binding). v1 (teal rounded), v2 (blaze boxy), v3 (champagne premium) all rejected as still reading AI-made — they are anti-reference, not foundation. Fresh visual worlds chosen 2026-09-05.

## Evidence on Hand

Live prod backend with a real 3-doc / 234-chunk corpus; saved RAGAS runs (prod `eval_3ad9de1e`: 0.89/0.93/0.91/1.0); retrieval debug per query. No mock data anywhere — future work must not fabricate content. UI screenshots pending from the owner.

## Product Principles

1. Evidence over decoration: every visual must trace to real pipeline output.
2. Operate first: scanability and task completion outrank expression on every route.
3. Real data only: empty states invite action; errors state what happened and the fix.
4. Contrast is a feature: dense telemetry must stay legible in all states.
