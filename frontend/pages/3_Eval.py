"""
Eval Dashboard Page — Run RAGAS evaluations and compare pipeline variants.

Features:
  - QA set selector and mode selection
  - Run evaluation and view per-question scores
  - Aggregate scorecard
  - Side-by-side comparison: vector-only vs hybrid+rerank
"""

import os

import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="Eval | Hybrid RAG", page_icon="📊", layout="wide")

def load_css():
    css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "style.css")
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ─── Custom CSS ──────────────────────────────────────────────────────────────
load_css()

BACKEND_URL = st.session_state.get("backend_url", "http://localhost:8000")

st.markdown("# 📊 Evaluation Dashboard")
st.markdown("Run RAGAS evaluations and compare retrieval modes.")
st.markdown("---")

# ─── Run New Evaluation ──────────────────────────────────────────────────────
st.markdown("### 🚀 Run New Evaluation")

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    qa_set_name = st.text_input(
        "QA Set Name",
        value="default",
        help="Name of the QA set file (without _qa_set.json suffix)",
    )

with col2:
    eval_mode = st.selectbox(
        "Retrieval Mode",
        ["hybrid", "vector_only"],
        help="Run evaluation in hybrid or vector-only mode",
    )

with col3:
    st.markdown("")  # Spacing
    st.markdown("")
    run_eval = st.button("▶️ Run Evaluation", use_container_width=True)

if run_eval:
    with st.spinner(f"Running {eval_mode} evaluation on '{qa_set_name}' QA set... This may take a few minutes."):
        try:
            response = requests.post(
                f"{BACKEND_URL}/eval/run",
                json={
                    "qa_set_name": qa_set_name,
                    "mode": eval_mode,
                },
                timeout=600,  # Eval can take a while
            )

            if response.status_code == 200:
                result = response.json()
                st.success(f"✅ Evaluation complete! Run ID: **{result['run_id']}**")

                # Show aggregate scores
                scores = result.get("scores", {})
                st.markdown("### 📈 Aggregate Scores")

                score_cols = st.columns(4)
                metrics = [
                    ("Faithfulness", scores.get("faithfulness")),
                    ("Answer Relevancy", scores.get("answer_relevancy")),
                    ("Context Precision", scores.get("context_precision")),
                    ("Context Recall", scores.get("context_recall")),
                ]

                for col, (label, value) in zip(score_cols, metrics):
                    with col:
                        display = f"{value:.4f}" if value is not None else "N/A"
                        st.metric(label, display)

                # Per-question breakdown
                per_q = result.get("per_question_breakdown", [])
                if per_q:
                    st.markdown("### 📋 Per-Question Breakdown")
                    df = pd.DataFrame(per_q)
                    display_cols = ["question", "faithfulness", "answer_relevancy",
                                    "context_precision", "context_recall"]
                    available = [c for c in display_cols if c in df.columns]
                    st.dataframe(df[available], use_container_width=True, height=400)

            elif response.status_code == 404:
                st.error(f"QA set '{qa_set_name}' not found. Check data/qa_sets/ directory.")
            else:
                st.error(f"Error: {response.json().get('detail', response.text)}")

        except requests.ConnectionError:
            st.error(f"❌ Cannot connect to backend at {BACKEND_URL}")
        except Exception as e:
            st.error(f"Error: {e}")

# ─── Past Runs ────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📜 Past Evaluation Runs")

try:
    response = requests.get(f"{BACKEND_URL}/eval/runs", timeout=10)
    if response.status_code == 200:
        runs = response.json()
        if runs:
            runs_df = pd.DataFrame(runs)
            st.dataframe(runs_df, use_container_width=True)

            # ── Comparison ────────────────────────────────────────────
            st.markdown("---")
            st.markdown("### 🔄 Compare Two Runs")
            st.markdown("Select two runs to compare side-by-side (e.g., vector_only vs hybrid).")

            run_ids = [r["run_id"] for r in runs]

            col1, col2 = st.columns(2)
            with col1:
                run1 = st.selectbox("Run 1 (baseline)", run_ids, key="compare_run1")
            with col2:
                run2_options = [r for r in run_ids if r != run1]
                if run2_options:
                    run2 = st.selectbox("Run 2 (comparison)", run2_options, key="compare_run2")
                else:
                    run2 = None
                    st.info("Need at least 2 runs to compare.")

            if run2 and st.button("📊 Compare", use_container_width=True):
                with st.spinner("Comparing runs..."):
                    try:
                        comp_response = requests.post(
                            f"{BACKEND_URL}/eval/compare",
                            params={"run_id_1": run1, "run_id_2": run2},
                            timeout=30,
                        )

                        if comp_response.status_code == 200:
                            comp = comp_response.json()

                            # Side-by-side metrics
                            st.markdown("#### Side-by-Side Comparison")

                            r1 = comp.get("run_1", {})
                            r2 = comp.get("run_2", {})
                            delta = comp.get("delta", {})

                            header_cols = st.columns([2, 1, 1, 1])
                            header_cols[0].markdown("**Metric**")
                            header_cols[1].markdown(f"**{r1.get('mode', 'Run 1')}**")
                            header_cols[2].markdown(f"**{r2.get('mode', 'Run 2')}**")
                            header_cols[3].markdown("**Delta**")

                            for metric in ["faithfulness", "answer_relevancy",
                                           "context_precision", "context_recall"]:
                                cols = st.columns([2, 1, 1, 1])
                                cols[0].write(metric.replace("_", " ").title())

                                s1 = r1.get("scores", {}).get(metric)
                                s2 = r2.get("scores", {}).get(metric)
                                d = delta.get(metric)

                                cols[1].write(f"{s1:.4f}" if s1 is not None else "N/A")
                                cols[2].write(f"{s2:.4f}" if s2 is not None else "N/A")

                                if d is not None:
                                    arrow = "↑" if d > 0 else "↓" if d < 0 else "="
                                    color = "comparison-better" if d > 0 else "comparison-worse" if d < 0 else ""
                                    cols[3].markdown(
                                        f'<span class="{color}">{arrow} {abs(d):.4f}</span>',
                                        unsafe_allow_html=True,
                                    )
                                else:
                                    cols[3].write("N/A")

                            # Summary
                            summary = comp.get("summary", "")
                            if summary:
                                st.markdown("#### Summary")
                                st.code(summary, language="text")

                        else:
                            st.error(f"Comparison error: {comp_response.text}")
                    except Exception as e:
                        st.error(f"Error: {e}")
        else:
            st.info("No evaluation runs yet. Run your first evaluation above!")
    else:
        st.warning("Could not fetch past runs.")
except requests.ConnectionError:
    st.info("Start the backend to see evaluation history.")
except Exception:
    st.info("Start the backend to see evaluation history.")
