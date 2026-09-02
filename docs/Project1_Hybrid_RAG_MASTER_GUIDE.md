# PROJECT 01 — Hybrid RAG System with Embedded Evaluation Harness
**Difficulty:** ●●●●○ Advanced | **Est. total time:** ~14–17 days part-time

---

## 1. Ideation — Why This Project, Why It's Different

Every bootcamp grad has a "RAG chatbot over my PDFs" repo. Almost none of them can
answer the one question every hiring manager will actually ask: *"How do you know
it's retrieving the right thing?"* — because they never measured it. They built a
vector-search-and-pray system and called it RAG.

This project forces two things most tutorials skip:

1. **A retrieval pipeline that's actually hybrid** — keyword (BM25) catches exact
   terms/IDs/names that embeddings blur over; vector search catches paraphrases and
   semantic matches BM25 misses. Fusing them + reranking is what production RAG
   systems (Notion AI, Perplexity, internal enterprise search) actually do.
2. **An instrument that proves it works** — a real evaluation harness (RAGAS) run
   against a held-out QA set, so every pipeline change is judged by numbers, not
   vibes. This is the actual skill gap companies hire for in 2026: not "can you
   call an embedding API" but "can you measure and improve retrieval quality."

**The interview story you're building toward:** *"I built hybrid retrieval, proved
it beats vector-only with RAGAS scores, and used those scores to drive every
pipeline decision I made afterward."*

---

## 2. Goals vs. Non-Goals

### In scope (v1)
- Real document corpus ingestion with context-aware chunking (not fixed-size windows)
- Open-source embeddings (BGE family), local vector store
- Hybrid retrieval: BM25 + vector search, fused with Reciprocal Rank Fusion (RRF)
- Cross-encoder reranking stage on top of the fused candidates
- Context compression (trim chunks to the relevant span, not full chunk dumps)
- Citations on every generated answer, traceable to source chunk(s)
- RAGAS evaluation harness: faithfulness, answer relevancy, context precision/recall
- Before/after comparison: vector-only vs. hybrid+rerank, with numbers

### Explicitly out of scope (v1)
- Multi-modal documents (images, tables-as-images) — text only
- Multi-turn conversational memory — single-shot Q&A only
- Multi-tenant auth / user accounts

### Stretch goals (only after v1 is solid)
- Semantic cache in front of the generator (reuse Project 03 as a drop-in)
- Incremental re-indexing when source docs change, without a full rebuild
- Query-rewriting step (decompose multi-part questions before retrieval)

---

## 3. Success Metrics (what "done" looks like)
- [ ] RAGAS faithfulness score ≥ 0.8 on your held-out QA set
- [ ] Hybrid+rerank retrieval demonstrably beats vector-only on the same eval set —
      you must produce and show this comparison, not just claim it
- [ ] Every answer in the demo UI shows its source citation(s)
- [ ] Eval harness runs as a single command and outputs a scorecard

---

## 4. Architecture & Workflow

```
Documents
  -> Loader (PDF / MD / TXT)
  -> Context-aware chunker (split on headers/sections/paragraphs first;
     fall back to size-based splitting only for oversized paragraphs)
  -> Embedding model (BGE-small/base, runs on CPU)
  -> Vector store (ChromaDB, local, on-disk)
  -> BM25 index (rank_bm25, pure Python, in-memory/on-disk)

Query
  -> Embed query
  -> Parallel: vector search (top-K) + BM25 search (top-K)
  -> Fusion (Reciprocal Rank Fusion) -> merged candidate list
  -> Cross-encoder reranker (ms-marco-MiniLM-L-6-v2) -> top-N
  -> Context compression (trim to relevant spans within each chunk)
  -> Prompt assembly with citation metadata
  -> LLM generation (Claude API, Haiku for dev / Sonnet for final demo)
  -> Answer + citations returned

Eval (offline, on-demand)
  -> Held-out QA set (question, ground-truth answer, ground-truth chunk IDs)
  -> Run full pipeline per question
  -> RAGAS metrics: faithfulness, answer_relevancy, context_precision, context_recall
  -> Scorecard output (JSON + a simple table) saved per run for comparison
```

---

## 5. Tech Stack (and why)

| Layer | Choice | Why |
|---|---|---|
| Backend | FastAPI | Async, trivial to instrument/log |
| Embeddings | `BAAI/bge-small-en-v1.5` via `sentence-transformers` | Runs fine on CPU — important since your embedding/indexing work shouldn't depend on your GTX 1650's 4GB VRAM |
| Vector store | ChromaDB (local, zero-infra) | Persists to disk, no server process to babysit on a laptop with limited RAM |
| Keyword search | `rank_bm25` | Pure Python, no infra, good enough at this corpus scale |
| Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Small enough to run on CPU in reasonable time |
| LLM | Claude API (Haiku in dev, Sonnet for the demo) | Keeps local compute and cost low |
| Eval | `ragas` + a self-authored QA set (20–40 pairs) | Industry-standard RAG eval metrics |
| Frontend | Streamlit | Fast to build, reusable skill across all 3 projects |
| Persistence | SQLite | Chunk metadata + citation mapping, zero-config |

### Hardware reality check (Lenovo IdeaPad Gaming 3, i5-10300H, GTX 1650, 16GB RAM)
- Nothing in this stack needs the GPU. Embedding + reranking with the small models
  above run acceptably on CPU at this corpus scale (hundreds of chunks, not millions).
- Don't run ChromaDB + a local LLM + Docker + your IDE all at once if you're tight
  on RAM — you don't need a local LLM here at all; the Claude API replaces it.
- If indexing feels slow, batch your embedding calls (encode in batches of 32–64)
  instead of one chunk at a time.

---

## 6. Data Model

**Document** — `doc_id, source_path, title, ingested_at`

**Chunk** — `chunk_id, doc_id, text, start_offset, end_offset, embedding_vector_id (FK), token_count`

**QAEvalItem** — `qa_id, question, ground_truth_answer, ground_truth_chunk_ids[]`

**EvalRun** — `run_id, timestamp, config_snapshot (chunking strategy, retrieval weights, model versions), per_question_scores, aggregate_scores`

---

## 7. API Contract

```
POST /ingest
  body: { source_path | raw_text, title }
  -> chunks, embeds, indexes the document

POST /query
  body: { question, top_k (default 5) }
  -> { answer,
       citations: [{ chunk_id, doc_title, snippet }],
       retrieval_debug: { bm25_hits, vector_hits, reranked_order } }

POST /eval/run
  body: { qa_set_id | inline qa list }
  -> { run_id,
       scores: { faithfulness, answer_relevancy, context_precision, context_recall },
       per_question_breakdown }

GET /eval/runs/{run_id}
  -> stored scorecard, for comparing across pipeline changes
```

---

## 8. UI Pages / Screens (Streamlit)

1. **Ingest page** — file upload (PDF/MD/TXT), title field, "Ingest" button, shows
   chunk count + a sample of the first few chunks after processing.
2. **Ask a Question page** — chat-style input box, displays the answer with inline
   citation markers, an expandable "why this answer" panel showing: BM25 hits,
   vector hits, fused order, reranked order, and the final compressed context sent
   to the LLM.
3. **Eval Dashboard page** — dropdown to pick a QA set, "Run Eval" button, table of
   per-question scores, aggregate scorecard, and a side-by-side comparison view
   (vector-only run vs. hybrid+rerank run) with a simple bar/table comparison.
4. **(optional) Document Library page** — list of ingested documents with chunk
   counts and ingestion timestamps; delete/re-index action.

---

## 9. Build Plan — Phased TODO Checklist

### Phase 1 — Ingestion + naive retrieval (3–4 days)
- [ ] Set up FastAPI project skeleton + `requirements.txt` (fastapi, uvicorn,
      sentence-transformers, chromadb, rank_bm25, pypdf, ragas)
- [ ] Implement document loader for PDF (pypdf/pdfplumber) and plain MD/TXT
- [ ] Implement context-aware chunker: split on headers/sections first, paragraph
      fallback, hard size cap only as a last resort
- [ ] Load `bge-small-en-v1.5`, test embedding a handful of chunks, sanity-check
      vector shapes/dimensions
- [ ] Stand up a local persistent ChromaDB collection
- [ ] Wire loader → chunker → embed → store into the `/ingest` endpoint
- [ ] Implement a naive vector-only `/query` endpoint (embed query → top-k Chroma
      search → stuff chunks into prompt → call Claude Haiku → return answer)
- [ ] Manually sanity-check retrieval on 5–10 hand-picked questions against a real
      document set you actually care about

### Phase 2 — Hybrid retrieval + reranking (3–4 days)
- [ ] Build the BM25 index alongside the vector index (same chunk set, same IDs)
- [ ] Implement Reciprocal Rank Fusion to merge BM25 + vector result lists
- [ ] Add the cross-encoder reranker on the fused top-K candidates
- [ ] Log retrieval_debug (bm25_hits, vector_hits, reranked_order) for every query
- [ ] Manually compare retrieved chunks before/after hybrid+rerank on the same
      5–10 questions from Phase 1 — write down what changed and why

### Phase 3 — Context compression + citations (2 days)
- [ ] Implement a compression step that trims each retrieved chunk down to the
      sentence span actually relevant to the query (use reranker scores or a
      cheap extraction heuristic — don't over-engineer this)
- [ ] Wire chunk_id/doc_title/snippet metadata through to the final API response
- [ ] Confirm every answer in `/query` carries at least one citation

### Phase 4 — Eval harness (3–4 days)
- [ ] Author your held-out QA set (20–40 Q&A pairs, each tied to known
      ground-truth chunk IDs) **before** you over-tune the pipeline — do this
      first to avoid biasing your own eval
- [ ] Install and wire up `ragas`; run a baseline (vector-only) scorecard
- [ ] Re-run after switching to hybrid+rerank; save both scorecards via `EvalRun`
- [ ] Produce a clear before/after comparison table (vector-only vs hybrid+rerank)
- [ ] Treat any RAGAS regression after a pipeline change as a failing test, not
      just a metric to shrug at

### Phase 5 — Frontend + deploy (2–3 days)
- [ ] Build the Streamlit pages from Section 8
- [ ] Deploy FastAPI backend + Streamlit frontend (Render/Railway free tier, or a
      single container running both)
- [ ] Keep the vector store + SQLite as on-disk volumes so state survives restarts
- [ ] Write the README with the eval scorecard front and center (see Section 11)

---

## 10. Testing Strategy
- [ ] Unit test the RRF fusion function with synthetic ranked lists where you
      know the expected merged order ahead of time
- [ ] Unit test the chunker against a document with known section boundaries —
      assert chunk boundaries land where expected
- [ ] Treat the eval harness itself as your integration test: a regression in
      RAGAS scores after a code change should block you from moving on, same as
      a failing unit test would

---

## 11. Deliverables Checklist
- [ ] GitHub repo with a clear README: problem statement → architecture →
      eval scorecard (front and center) → how to run it locally
- [ ] Held-out QA set committed to the repo (so the eval is reproducible)
- [ ] Before/after comparison table (vector-only vs hybrid+rerank) in the README
- [ ] Short demo video or GIF: upload a doc, ask a question, show the citation
      and the "why this answer" debug panel
- [ ] Live deployed link (Render/Railway free tier) if you want it in your resume

---

## 12. Resume Line (target)
> "Built a hybrid retrieval RAG system (BM25 + vector + cross-encoder reranking)
> with a RAGAS evaluation harness measuring faithfulness and context precision,
> deployed as a FastAPI + Streamlit service."

## 13. Skills You'll Walk Away With
Retrieval architecture, embedding/reranking tradeoffs, prompt context engineering,
evaluation-driven iteration, citation grounding.
