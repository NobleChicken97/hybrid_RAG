"""
Ask Page — Question answering with citations and retrieval debug.

Features:
  - Chat-style input for questions
  - Answer display with inline citation markers
  - Expandable "Why this answer?" debug panel showing full retrieval pipeline
"""

import streamlit as st
import requests
import json
import os

st.set_page_config(page_title="Ask | Hybrid RAG", page_icon="💬", layout="wide")

def load_css():
    css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "style.css")
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ─── Custom CSS ──────────────────────────────────────────────────────────────
load_css()

BACKEND_URL = st.session_state.get("backend_url", "http://localhost:8000")

st.markdown("# 💬 Ask a Question")
st.markdown("Get answers with citations from your ingested documents.")
st.markdown("---")

# ─── Query Controls ──────────────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])

with col1:
    question = st.text_input(
        "Your Question",
        placeholder="What would you like to know?",
        label_visibility="collapsed",
    )

with col2:
    mode = st.selectbox(
        "Retrieval Mode",
        ["hybrid", "vector_only"],
        help="Compare hybrid (BM25+vector+rerank) vs vector-only retrieval",
    )

col3, col4 = st.columns([1, 3])
with col3:
    top_k = st.slider("Top-K Results", min_value=1, max_value=20, value=5)

ask_button = st.button("🔍 Ask", use_container_width=True, disabled=not question)

# ─── Query & Display ─────────────────────────────────────────────────────────
if ask_button and question:
    with st.spinner("Searching and generating answer..."):
        try:
            response = requests.post(
                f"{BACKEND_URL}/query",
                json={
                    "question": question,
                    "top_k": top_k,
                    "mode": mode,
                },
                timeout=120,
            )

            if response.status_code == 200:
                result = response.json()

                # ── Answer ────────────────────────────────────────────
                st.markdown("### 📝 Answer")
                st.markdown(
                    f'<div class="answer-box">{result["answer"]}</div>',
                    unsafe_allow_html=True,
                )

                # ── Citations ─────────────────────────────────────────
                citations = result.get("citations", [])
                if citations:
                    st.markdown("### 📌 Citations")
                    for i, cit in enumerate(citations, 1):
                        st.markdown(
                            f"""<div class="chunk-card">
                                <div class="chunk-header">[{i}] {cit.get('doc_title', 'Unknown')}</div>
                                <div style="font-size: 0.8em; color: var(--color-charcoal); margin-bottom: 4px;">Chunk ID: {cit.get('chunk_id', 'N/A')}</div>
                                <div style="font-size: 0.9em; color: var(--color-charcoal); opacity: 0.8;">"{cit.get('snippet', '')}..."</div>
                            </div>""",
                            unsafe_allow_html=True,
                        )
                else:
                    st.info("No citations found for this answer.")

                # ── Debug Panel ───────────────────────────────────────
                debug = result.get("retrieval_debug", {})

                with st.expander("🔧 Why this answer? (Retrieval Debug)", expanded=False):
                    tab_bm25, tab_vector, tab_fused, tab_reranked = st.tabs([
                        "BM25 Hits", "Vector Hits", "Fused Order", "Reranked"
                    ])

                    with tab_bm25:
                        hits = debug.get("bm25_hits", [])
                        score_label = "score"
                        if hits:
                            for hit in hits[:10]:
                                st.markdown(
                                    f"""<div class="chunk-card" style="border-left: 3px solid var(--color-sage-wash);">
                                        <div class="chunk-header">{hit['chunk_id']} ({score_label}: {hit['score']:.4f})</div>
                                        <div style="color: var(--color-true-black);">{hit['text_preview']}...</div>
                                    </div>""",
                                    unsafe_allow_html=True,
                                )
                        else:
                            st.info("No BM25 hits.")

                    with tab_vector:
                        hits = debug.get("vector_hits", [])
                        score_label = "similarity"
                        if hits:
                            for hit in hits[:10]:
                                st.markdown(
                                    f"""<div class="chunk-card" style="border-left: 3px solid var(--color-sage-wash);">
                                        <div class="chunk-header">{hit['chunk_id']} ({score_label}: {hit['score']:.4f})</div>
                                        <div style="color: var(--color-true-black);">{hit['text_preview']}...</div>
                                    </div>""",
                                    unsafe_allow_html=True,
                                )
                        else:
                            st.info("No vector hits.")

                    with tab_fused:
                        hits = debug.get("fused_order", [])
                        score_label = "RRF"
                        if hits:
                            for hit in hits[:10]:
                                st.markdown(
                                    f"""<div class="chunk-card" style="border-left: 3px solid var(--color-sage-wash);">
                                        <div class="chunk-header">{hit['chunk_id']} ({score_label}: {hit['score']:.4f})</div>
                                        <div style="color: var(--color-true-black);">{hit['text_preview']}...</div>
                                    </div>""",
                                    unsafe_allow_html=True,
                                )
                        else:
                            st.info("No fused hits.")

                    with tab_reranked:
                        hits = debug.get("reranked_order", [])
                        score_label = "cross-encoder"
                        if hits:
                            for i, hit in enumerate(hits[:10], 1):
                                st.markdown(
                                    f"""<div class="chunk-card" style="border-left: 3px solid var(--color-sage-wash);">
                                        <div class="chunk-header">#{i} {hit['chunk_id']} ({score_label}: {hit['score']:.4f})</div>
                                        <div style="color: var(--color-true-black);">{hit['text_preview']}...</div>
                                    </div>""",
                                    unsafe_allow_html=True,
                                )
                        else:
                            st.info("No reranked hits.")

                # Store in session for history
                if "query_history" not in st.session_state:
                    st.session_state["query_history"] = []
                st.session_state["query_history"].append({
                    "question": question,
                    "answer": result["answer"],
                    "mode": mode,
                    "citations": len(citations),
                })

            elif response.status_code == 400:
                st.warning(response.json().get("detail", "Bad request"))
            else:
                st.error(f"Error {response.status_code}: {response.text}")

        except requests.ConnectionError:
            st.error(
                f"❌ Cannot connect to backend at {BACKEND_URL}. "
                "Make sure the FastAPI server is running."
            )
        except Exception as e:
            st.error(f"Error: {e}")

# ─── Query History ────────────────────────────────────────────────────────────
if st.session_state.get("query_history"):
    st.markdown("---")
    st.markdown("### 📜 Recent Queries")
    for i, entry in enumerate(reversed(st.session_state["query_history"][-5:])):
        with st.expander(f"Q: {entry['question'][:80]}... ({entry['mode']})"):
            st.write(entry["answer"])
            st.caption(f"Mode: {entry['mode']} | Citations: {entry['citations']}")
