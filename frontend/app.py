"""
Streamlit frontend for the Hybrid RAG System.

Multi-page app with:
  1. Ingest — Upload and process documents
  2. Ask — Question answering with citations
  3. Eval — Evaluation dashboard with run comparison
"""

import streamlit as st

# ─── Page Configuration ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="Hybrid RAG System",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

import os


def load_css():
    css_path = os.path.join(os.path.dirname(__file__), "style.css")
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ─── Custom CSS ──────────────────────────────────────────────────────────────
load_css()

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("# 🔍 Hybrid RAG")
    st.markdown("---")

    # Backend URL configuration
    backend_url = st.text_input(
        "Backend URL",
        value="http://localhost:8000",
        help="The URL of the FastAPI backend",
    )
    st.session_state["backend_url"] = backend_url

    # Health check
    if st.button("🏥 Check Health"):
        try:
            import requests
            response = requests.get(f"{backend_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                st.success("Backend is healthy!")
                col1, col2 = st.columns(2)
                col1.metric("📄 Documents", data.get("documents_count", 0))
                col2.metric("📦 Chunks", data.get("chunks_count", 0))
                
                col3, col4 = st.columns(2)
                col3.metric("📊 Eval Runs", data.get("eval_runs_count", 0))
                
                st.markdown("---")
                st.markdown("### System Config")
                env = data.get("environment", "unknown")
                st.write(f"**Environment**: `{env}`")
                st.write(f"**LLM Backend**: `{data.get('llm_backend', 'unknown')}`")
                
                if env == "local":
                    st.info("Currently running with local models. Cloud options are still available.")
                elif env == "production":
                    st.warning("Production Mode: Local models (Ollama) are disabled.")
            else:
                st.error(f"Backend returned status {response.status_code}")
        except Exception as e:
            st.error(f"Cannot connect to backend: {e}")

    st.markdown("---")
    st.markdown(
        "**Architecture**: BM25 + Vector → RRF → Reranker → Compression → LLM"
    )
    st.markdown(
        "Built with FastAPI, ChromaDB, BGE-small, ms-marco reranker, and Claude."
    )

# ─── Main Page ───────────────────────────────────────────────────────────────
st.markdown("# 🔍 Hybrid RAG System")
st.markdown(
    "A production-grade retrieval-augmented generation pipeline with hybrid retrieval, "
    "cross-encoder reranking, context compression, and RAGAS evaluation."
)

st.markdown("---")

# Feature cards
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 📄 Ingest")
    st.markdown(
        "Upload PDF, Markdown, or text documents. "
        "Context-aware chunking preserves document structure."
    )
    st.page_link("pages/1_Ingest.py", label="Go to Ingest →", icon="📄")

with col2:
    st.markdown("### 💬 Ask")
    st.markdown(
        "Ask questions and get cited answers. "
        "See the full retrieval debug — BM25, vector, fusion, reranking."
    )
    st.page_link("pages/2_Ask.py", label="Go to Ask →", icon="💬")

with col3:
    st.markdown("### 📊 Evaluate")
    st.markdown(
        "Run RAGAS evaluations and compare vector-only vs hybrid+rerank "
        "with side-by-side scorecards."
    )
    st.page_link("pages/3_Eval.py", label="Go to Eval →", icon="📊")

# Architecture diagram
st.markdown("---")
st.markdown("### 🏗️ Architecture")
st.code("""
Documents → Loader (PDF/MD/TXT) → Context-aware Chunker → BGE Embeddings
         → ChromaDB (vector) + BM25 Index (keyword)

Query → Embed Query → Parallel: Vector Search + BM25 Search
     → RRF Fusion → Cross-encoder Reranker → Context Compression
     → Prompt Assembly + Citations → Claude LLM → Answer + Citations

Eval → Held-out QA Set → Full Pipeline → RAGAS Metrics → Scorecard
""", language="text")
