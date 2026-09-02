"""
RAGAS evaluation harness.

Runs the full RAG pipeline on each QA pair and feeds results to RAGAS
for scoring on: faithfulness, answer_relevancy, context_precision, context_recall.

This is THE differentiator of this project — it proves the pipeline works
with numbers, not vibes.
"""

import json
import uuid

from app.config import get_settings
from app.database import EvalRun, get_session_factory
from app.generation.llm import generate
from app.generation.prompt import SYSTEM_PROMPT, build_prompt
from app.ingestion.embedder import embed_query
from app.models import EvalScores, QAItem, QuestionScore
from app.retrieval import bm25_index, vector_store
from app.retrieval.compressor import compress_context
from app.retrieval.fusion import fuse
from app.retrieval.reranker import rerank


def _run_pipeline(question: str, mode: str = "hybrid", top_k: int | None = None) -> tuple[str, list[str]]:
    """
    Run the retrieval + generation pipeline for a single question.

    Returns:
        Tuple of (answer, list_of_retrieved_context_texts).
    """
    settings = get_settings()
    if top_k is None:
        top_k = settings.rerank_top_n

    # Vector search
    query_embedding = embed_query(question)
    vector_results = vector_store.search(query_embedding, top_k=settings.retrieval_top_k)

    if mode == "hybrid":
        # BM25 search
        bm25_results = bm25_index.search(question, top_k=settings.retrieval_top_k)

        # RRF fusion
        fused = fuse(
            bm25_results=[(r.chunk_id, r.score, r.text) for r in bm25_results],
            vector_results=[(r.chunk_id, r.score, r.text) for r in vector_results],
            k=settings.rrf_k,
        )

        candidates = [(r.chunk_id, r.text, r.sources) for r in fused]
    else:
        candidates = [(r.chunk_id, r.text, ["vector"]) for r in vector_results]

    # Rerank
    reranked = rerank(question, candidates[:settings.retrieval_top_k], top_n=top_k)

    if not reranked:
        return "No relevant context found.", []

    # Compress context
    compressed = compress_context(question, [(r.chunk_id, r.text) for r in reranked])

    # Build prompt and generate
    context_for_prompt = []
    context_texts = []

    for comp in compressed:
        chunk_meta = vector_store.get_chunks_by_ids([comp.chunk_id])
        doc_title = chunk_meta[0].metadata.get("doc_title", "Unknown") if chunk_meta else "Unknown"
        context_for_prompt.append((comp.chunk_id, comp.compressed_text, doc_title))
        context_texts.append(comp.compressed_text)

    user_prompt = build_prompt(question, context_for_prompt)
    answer = generate(user_prompt, system_prompt=SYSTEM_PROMPT)

    return answer, context_texts


def run_evaluation(
    qa_items: list[QAItem],
    mode: str = "hybrid",
) -> tuple[str, EvalScores, list[QuestionScore]]:
    """
    Run the full evaluation harness.

    For each QA pair:
      1. Run the full retrieval + generation pipeline
      2. Collect question, answer, contexts, ground_truth
      3. Feed to RAGAS for scoring

    Args:
        qa_items: List of QA evaluation items.
        mode: Retrieval mode ('hybrid' or 'vector_only').

    Returns:
        Tuple of (run_id, aggregate_scores, per_question_scores).
    """
    run_id = f"eval_{uuid.uuid4().hex[:8]}"
    settings = get_settings()

    print(f"\n[Eval] Starting evaluation run: {run_id}")
    print(f"[Eval] Mode: {mode} | QA pairs: {len(qa_items)}")

    # Collect results for RAGAS
    questions = []
    answers = []
    contexts_list = []
    ground_truths = []

    per_question_scores = []

    # Questions whose generation failed (e.g. cloud API errors) are kept out
    # of the RAGAS dataset: scoring the literal error string as an answer
    # produces meaningless zeros that poison the aggregate scorecard.
    failed_questions: list[QuestionScore] = []

    for i, qa in enumerate(qa_items):
        print(f"[Eval] Processing question {i + 1}/{len(qa_items)}: {qa.question[:60]}...")

        try:
            answer, contexts = _run_pipeline(qa.question, mode=mode)
        except Exception as e:
            print(f"[Eval] Generation failed on question {i + 1}, excluding from scoring: {e}")
            failed_questions.append(QuestionScore(question=qa.question, answer=f"Error: {e}"))
            continue

        questions.append(qa.question)
        answers.append(answer)
        contexts_list.append(contexts)
        ground_truths.append(qa.ground_truth_answer)

    # --- Run RAGAS evaluation ---
    aggregate_scores = EvalScores()

    try:
        from datasets import Dataset

        if not questions:
            # Raise so the outer handler skips RAGAS cleanly instead of
            # evaluating an empty dataset.
            raise RuntimeError("all questions failed generation; nothing to score")

        eval_dataset = Dataset.from_dict({
            "question": questions,
            "answer": answers,
            "contexts": contexts_list,
            "ground_truth": ground_truths,
        })

        try:
            import pandas as pd
            from ragas import evaluate
            from ragas.metrics import (
                answer_relevancy,
                context_precision,
                context_recall,
                faithfulness,
            )

            # Configure RAGAS judge backend.
            # NOTE: ragas >= 0.4 no longer honours the legacy OPENAI_* env vars,
            # so we pass an explicit judge LLM (and local embeddings) instead.
            judge_llm = None
            judge_embeddings = None
            if settings.ragas_judge_backend in ("cerebras", "groq", "gemini"):
                base_by_backend = {
                    "cerebras": settings.cerebras_base_url,
                    "groq": settings.groq_base_url,
                    "gemini": settings.gemini_base_url,
                }
                key_by_backend = {
                    "cerebras": settings.cerebras_api_key,
                    "groq": settings.groq_api_key,
                    "gemini": settings.gemini_api_key,
                }
                from langchain_community.embeddings import HuggingFaceEmbeddings
                from langchain_openai import ChatOpenAI
                from ragas.embeddings import LangchainEmbeddingsWrapper
                from ragas.llms import LangchainLLMWrapper

                judge_llm = LangchainLLMWrapper(
                    ChatOpenAI(
                        model=settings.ragas_judge_model,
                        base_url=base_by_backend[settings.ragas_judge_backend],
                        api_key=key_by_backend[settings.ragas_judge_backend],
                        temperature=0,
                        # Free-tier endpoints drop connections during long evals;
                        # SDK-level retries absorb transient failures before
                        # ragas marks the whole job as NaN.
                        timeout=120,
                        max_retries=3,
                    ),
                    # Gemini's OpenAI-compatible endpoint rejects n>1
                    # ("Multiple candidates is not enabled"). bypass_n makes
                    # ragas send n separate requests instead of setting n.
                    bypass_n=True,
                )
                # Local HF embeddings for answer_relevancy: deterministic and
                # avoids an extra cloud-embedding dependency on the free tier.
                judge_embeddings = LangchainEmbeddingsWrapper(
                    HuggingFaceEmbeddings(model_name=settings.embedding_model)
                )

            from ragas.run_config import RunConfig

            # Generous timeout: judge calls on free-tier Gemini can be slow,
            # and context_precision sends per-context verdict prompts.
            results = evaluate(
                eval_dataset,
                metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
                llm=judge_llm,
                embeddings=judge_embeddings,
                run_config=RunConfig(max_workers=4, timeout=600, max_wait=30),
            )

            def _mean_or_none(df: "pd.DataFrame", col: str):
                if col not in df.columns:
                    return None
                series = pd.to_numeric(df[col], errors="coerce").dropna()
                return round(float(series.mean()), 4) if len(series) else None

            # ragas >= 0.4 returns an EvaluationDataset; older versions return
            # a dict-like result. Handle both.
            if hasattr(results, "to_pandas"):
                result_df = results.to_pandas()

                aggregate_scores = EvalScores(
                    faithfulness=_mean_or_none(result_df, "faithfulness"),
                    answer_relevancy=_mean_or_none(result_df, "answer_relevancy"),
                    context_precision=_mean_or_none(result_df, "context_precision"),
                    context_recall=_mean_or_none(result_df, "context_recall"),
                )

                # Per-question scores from the RAGAS result dataframe
                for idx, row in result_df.iterrows():
                    def _val(col, _row=row):
                        v = _row.get(col) if col in result_df.columns else None
                        if v is None or (isinstance(v, float) and pd.isna(v)):
                            return None
                        return round(float(v), 4)

                    per_question_scores.append(
                        QuestionScore(
                            question=questions[idx] if idx < len(questions) else str(row.get("user_input", "")),
                            answer=answers[idx] if idx < len(answers) else str(row.get("response", "")),
                            faithfulness=_val("faithfulness"),
                            answer_relevancy=_val("answer_relevancy"),
                            context_precision=_val("context_precision"),
                            context_recall=_val("context_recall"),
                        )
                    )
            else:
                aggregate_scores = EvalScores(
                    faithfulness=results.get("faithfulness"),
                    answer_relevancy=results.get("answer_relevancy"),
                    context_precision=results.get("context_precision"),
                    context_recall=results.get("context_recall"),
                )

        except ImportError:
            print("[Eval] RAGAS not installed. Computing basic metrics only.")
            # Fallback: no RAGAS scores, just collect the Q&A pairs
        except Exception as e:
            print(f"[Eval] RAGAS evaluation error: {e}")
            print("[Eval] Saving results without RAGAS scores.")

    except Exception as e:
        print(f"[Eval] Dataset creation error: {e}")

    # Fill per-question scores if RAGAS didn't produce them
    if not per_question_scores:
        for i in range(len(questions)):
            per_question_scores.append(
                QuestionScore(
                    question=questions[i],
                    answer=answers[i],
                )
            )

    # Failed generations stay visible in the per-question breakdown with null
    # scores, but were excluded from the RAGAS dataset above.
    per_question_scores.extend(failed_questions)
    if failed_questions:
        print(f"[Eval] WARNING: {len(failed_questions)}/{len(qa_items)} questions failed generation "
              f"and were excluded from aggregate scores.")

    # --- Save to database ---
    try:
        SessionLocal = get_session_factory()
        db = SessionLocal()

        # Record the concrete model alongside the backend: backends support
        # multiple models and scorecards are only interpretable with the
        # exact generator + judge identified.
        generation_models = {
            "cerebras": settings.cerebras_model,
            "groq": settings.groq_model,
            "gemini": settings.gemini_model,
            "claude": "claude-3-haiku",
        }
        config_snapshot = {
            "mode": mode,
            "embedding_model": settings.embedding_model,
            "reranker_model": settings.reranker_model,
            "retrieval_top_k": settings.retrieval_top_k,
            "rerank_top_n": settings.rerank_top_n,
            "rrf_k": settings.rrf_k,
            "generation_backend": settings.llm_backend,
            "generation_model": generation_models.get(settings.llm_backend),
            "judge_backend": settings.ragas_judge_backend,
            "judge_model": settings.ragas_judge_model,
        }

        eval_run = EvalRun(
            run_id=run_id,
            retrieval_mode=mode,
            config_snapshot=json.dumps(config_snapshot),
            faithfulness=aggregate_scores.faithfulness,
            answer_relevancy=aggregate_scores.answer_relevancy,
            context_precision=aggregate_scores.context_precision,
            context_recall=aggregate_scores.context_recall,
            per_question_scores=json.dumps([s.model_dump() for s in per_question_scores]),
        )

        db.add(eval_run)
        db.commit()
        db.close()
        print(f"[Eval] Run saved: {run_id}")

    except Exception as e:
        print(f"[Eval] Failed to save run: {e}")

    print("\n[Eval] === Evaluation Complete ===")
    print(f"[Eval] Run ID: {run_id}")
    print(f"[Eval] Faithfulness:      {aggregate_scores.faithfulness}")
    print(f"[Eval] Answer Relevancy:  {aggregate_scores.answer_relevancy}")
    print(f"[Eval] Context Precision: {aggregate_scores.context_precision}")
    print(f"[Eval] Context Recall:    {aggregate_scores.context_recall}")

    return run_id, aggregate_scores, per_question_scores
