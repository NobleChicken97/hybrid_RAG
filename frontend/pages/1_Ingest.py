"""
Ingest Page — Upload and process documents into the RAG system.

Features:
  - File upload (PDF/MD/TXT) or paste raw text
  - Shows chunk count and preview of first chunks after processing
  - Document library view
"""

import requests
import streamlit as st

st.set_page_config(page_title="Ingest | Hybrid RAG", page_icon="📄", layout="wide")

import os


def load_css():
    css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "style.css")
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ─── Custom CSS ──────────────────────────────────────────────────────────────
load_css()

BACKEND_URL = st.session_state.get("backend_url", "http://localhost:8000")

st.markdown("# 📄 Document Ingestion")
st.markdown("Upload documents to build the knowledge base for the RAG system.")
st.markdown("---")

# ─── Upload Section ──────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["📁 Upload File", "📝 Paste Text"])

with tab1:
    st.markdown("### Upload a Document")
    uploaded_file = st.file_uploader(
        "Choose a PDF, Markdown, or Text file",
        type=["pdf", "md", "markdown", "txt"],
        help="Supported formats: PDF, Markdown (.md), Plain Text (.txt)",
    )
    title_file = st.text_input(
        "Document Title",
        value="",
        placeholder="Enter a title for this document...",
        key="file_title",
    )

    if st.button("🚀 Ingest Document", key="ingest_file", disabled=uploaded_file is None) and uploaded_file is not None:
        title = title_file if title_file else uploaded_file.name
            with st.spinner("Processing document..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                    data = {"title": title}
                    response = requests.post(
                        f"{BACKEND_URL}/ingest",
                        files=files,
                        data=data,
                        timeout=120,
                    )

                    if response.status_code == 200:
                        result = response.json()
                        st.success(
                            f"✅ Document ingested! "
                            f"**{result['chunk_count']}** chunks created."
                        )

                        # Show chunk previews
                        st.markdown("### Chunk Previews")
                        for chunk in result.get("sample_chunks", []):
                            st.markdown(
                                f"""<div class="chunk-card">
                                <div class="chunk-header">
                                    📦 {chunk['chunk_id']} | {chunk['token_count']} tokens
                                    {(' | 📑 ' + chunk['section_header']) if chunk.get('section_header') else ''}
                                </div>
                                <div>{chunk['text_preview']}</div>
                                </div>""",
                                unsafe_allow_html=True,
                            )
                    else:
                        st.error(f"Error: {response.json().get('detail', response.text)}")
                except requests.ConnectionError:
                    st.error(
                        "❌ Cannot connect to backend. "
                        "Make sure the FastAPI server is running on "
                        f"{BACKEND_URL}"
                    )
                except Exception as e:
                    st.error(f"Error: {e}")

with tab2:
    st.markdown("### Paste Raw Text")
    raw_text = st.text_area(
        "Document Content",
        height=300,
        placeholder="Paste your document text here...",
    )
    title_text = st.text_input(
        "Document Title",
        value="",
        placeholder="Enter a title...",
        key="text_title",
    )

    if st.button("🚀 Ingest Text", key="ingest_text", disabled=not raw_text):
        title = title_text if title_text else "Pasted Document"
        with st.spinner("Processing text..."):
            try:
                data = {"title": title, "raw_text": raw_text}
                response = requests.post(
                    f"{BACKEND_URL}/ingest",
                    data=data,
                    timeout=120,
                )

                if response.status_code == 200:
                    result = response.json()
                    st.success(
                        f"✅ Text ingested! "
                        f"**{result['chunk_count']}** chunks created."
                    )

                    st.markdown("### Chunk Previews")
                    for chunk in result.get("sample_chunks", []):
                        st.markdown(
                            f"""<div class="chunk-card">
                            <div class="chunk-header">
                                📦 {chunk['chunk_id']} | {chunk['token_count']} tokens
                            </div>
                            <div>{chunk['text_preview']}</div>
                            </div>""",
                            unsafe_allow_html=True,
                        )
                else:
                    st.error(f"Error: {response.json().get('detail', response.text)}")
            except requests.ConnectionError:
                st.error(f"❌ Cannot connect to backend at {BACKEND_URL}")
            except Exception as e:
                st.error(f"Error: {e}")

# ─── Document Library ────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📚 System Status")

try:
    response = requests.get(f"{BACKEND_URL}/health", timeout=5)
    if response.status_code == 200:
        data = response.json()
        col1, col2, col3 = st.columns(3)
        col1.metric("📄 Documents", data.get("documents_count", 0))
        col2.metric("📦 Total Chunks", data.get("chunks_count", 0))
        col3.metric("📊 Eval Runs", data.get("eval_runs_count", 0))
    else:
        st.warning("Could not fetch system status.")
except Exception:
    st.info("Start the backend to see system status.")
