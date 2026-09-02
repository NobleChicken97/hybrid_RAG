# 🔍 Hybrid RAG System with Embedded Evaluation Harness

A production-grade Retrieval-Augmented Generation pipeline featuring hybrid retrieval (BM25 + vector), cross-encoder reranking, context compression, citation grounding, and a RAGAS evaluation harness — built to prove it works with numbers, not vibes.

> **Resume Line**: "Built a hybrid retrieval RAG system (BM25 + vector + cross-encoder reranking) with a RAGAS evaluation harness measuring faithfulness and context precision, deployed as a FastAPI + Streamlit service."

---

## 🏗️ Architecture

```
Documents → Loader (PDF/MD/TXT) → Context-aware Chunker → BGE Embeddings
         → ChromaDB (vector store) + BM25 Index (keyword search)

Query → Embed Query → Parallel: Vector Search + BM25 Search
     → Reciprocal Rank Fusion (RRF) → Cross-encoder Reranker
     → Context Compression → Prompt Assembly + Citations
     → Claude LLM → Answer + Citations

Eval → Held-out QA Set → Full Pipeline → RAGAS Metrics → Scorecard
```

---

## 📊 Evaluation Scorecard

| Metric | Vector-Only | Hybrid + Rerank | Delta |
|--------|-------------|-----------------|-------|
| Faithfulness | 1.000 | 1.000 | +0.000 |
| Answer Relevancy | 0.897 | **0.950** | +0.053 |
| Context Precision | **0.868** | 0.857 | −0.011 |
| Context Recall | 0.947 | **1.000** | +0.053 |

> 20-question held-out QA set, RAGAS 0.4 metrics. Hybrid run `eval_dc701f3b`, vector-only run `eval_7c8461c4` (2026-09-01/02): both arms use generator + judge `gemini-3.5-flash-lite`, **0 failed generations in either arm**, and identical corpora (4 documents, 432 chunks). Scores are means over all 20 questions.
>
> Reading: hybrid wins answer relevancy (+5.3) and context recall (+5.3, capturing every ground-truth evidence span), matches faithfulness, and trades −1.1 context precision — the reranked top-5 carries slightly more non-evidence text than pure vector search. With budget-conditional compression, both arms are strong; BM25 fusion's value shows where lexical terms matter.

> **History:** an earlier eval run was discarded — transient free-tier API failures were scored as answers, invalidating the baseline, and diagnosis (`diagnose_retrieval.py`) showed sentence-level compression was destroying ground-truth evidence on 13/20 questions (fixed: compression is now budget-conditional). Failed generations are now excluded from aggregate scores and reported separately. The compression fix lifted context_recall from 0.4 (discarded run) to 0.95–1.0 (clean runs).

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- An Anthropic API key ([get one here](https://console.anthropic.com/))

### Setup

```bash
# 1. Clone and navigate
cd "Hybrid RAG system"

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 5. Run both services
python run.py
```

The backend starts at **http://localhost:8000** (API docs at `/docs`).
The frontend starts at **http://localhost:8501**.

### Run Only Backend or Frontend

```bash
python run.py backend   # FastAPI only
python run.py frontend  # Streamlit only
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/ingest` | Ingest a document (file upload or raw text) |
| `POST` | `/query` | Ask a question, get answer + citations |
| `POST` | `/eval/run` | Run RAGAS evaluation on a QA set |
| `GET` | `/eval/runs` | List all evaluation runs |
| `GET` | `/eval/runs/{run_id}` | Get a specific run's scorecard |
| `POST` | `/eval/compare` | Compare two runs side-by-side |
| `GET` | `/health` | Health check with system stats |

Full API docs: **http://localhost:8000/docs**

---

## 🧪 Testing

```bash
# Run all unit tests
pytest tests/ -v

# Run specific test files
pytest tests/test_chunker.py -v
pytest tests/test_fusion.py -v
pytest tests/test_compressor.py -v
```

---

## 📁 Project Structure

```
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py             # Settings from .env
│   ├── database.py           # SQLAlchemy models (Document, Chunk, EvalRun)
│   ├── models.py             # Pydantic request/response schemas
│   ├── ingestion/
│   │   ├── loader.py         # PDF/MD/TXT document loaders
│   │   ├── chunker.py        # Context-aware chunking (headers→paragraphs→size)
│   │   └── embedder.py       # BGE-small embedding wrapper
│   ├── retrieval/
│   │   ├── vector_store.py   # ChromaDB wrapper
│   │   ├── bm25_index.py     # BM25 keyword search (rank_bm25)
│   │   ├── fusion.py         # Reciprocal Rank Fusion (RRF)
│   │   ├── reranker.py       # Cross-encoder reranker (ms-marco-MiniLM)
│   │   └── compressor.py     # Context compression (sentence-level)
│   ├── generation/
│   │   ├── llm.py            # Claude API client
│   │   ├── prompt.py         # Prompt templates with citation instructions
│   │   └── citations.py      # Citation extraction + formatting
│   ├── evaluation/
│   │   ├── harness.py        # RAGAS evaluation runner
│   │   ├── qa_loader.py      # QA set loader from JSON
│   │   └── scorecard.py      # Scorecard generation + comparison
│   └── api/
│       ├── ingest.py         # POST /ingest
│       ├── query.py          # POST /query
│       └── eval.py           # Eval endpoints
├── frontend/
│   ├── app.py                # Streamlit main app
│   └── pages/
│       ├── 1_Ingest.py       # Document upload page
│       ├── 2_Ask.py          # Q&A with citations + debug panel
│       └── 3_Eval.py         # Eval dashboard with comparison
├── data/
│   └── qa_sets/              # Held-out QA evaluation sets
├── sample_docs/              # Sample documents for testing
├── tests/                    # Unit tests
├── requirements.txt
├── run.py                    # Launch script
└── .env.example              # Environment variable template
```

### Repo tooling scripts

| Script | Purpose |
|--------|---------|
| `eval_full_run.py` | Runs the full QA set through the harness in both retrieval modes → `eval_results.json` |
| `eval_vector_only.py` | Re-captures only the vector-only arm (quota-probe-guarded) and merges it into `eval_results.json` |
| `diagnose_retrieval.py` | Traces ground-truth evidence through each retrieval stage (no LLM calls) — used to pinpoint the compression evidence loss |
| `dedupe_corpus.py` | One-shot corpus cleanup: removes duplicate documents, backfills content hashes |

---

## 🛠️ Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Backend | FastAPI | Async, auto-docs, easy to instrument |
| Embeddings | BGE-small-en-v1.5 | Runs on CPU, no GPU dependency |
| Vector Store | ChromaDB | Local, persistent, zero-infra |
| Keyword Search | rank_bm25 | Pure Python, no infra |
| Reranker | ms-marco-MiniLM-L-6-v2 | Small enough for CPU |
| LLM | Claude API | Low cost, high quality |
| Eval | RAGAS | Industry-standard RAG metrics |
| Frontend | Streamlit | Rapid UI development |
| Persistence | SQLite | Zero-config metadata store |

---

## 📋 License

MIT
