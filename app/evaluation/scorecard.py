"""
Scorecard generation and comparison for evaluation runs.

Produces structured scorecards and side-by-side comparison tables
for vector-only vs hybrid+rerank runs.
"""

from app.database import EvalRun, get_session_factory


def get_scorecard(run_id: str) -> dict:
    """
    Get the full scorecard for an evaluation run.

    Returns:
        Dict with run metadata, aggregate scores, and per-question breakdown.
    """
    SessionLocal = get_session_factory()
    db = SessionLocal()

    try:
        run = db.query(EvalRun).filter(EvalRun.run_id == run_id).first()
        if not run:
            return {"error": f"Run not found: {run_id}"}

        return {
            "run_id": run.run_id,
            "timestamp": run.timestamp.isoformat() if run.timestamp else None,
            "retrieval_mode": run.retrieval_mode,
            "config": run.get_config(),
            "scores": {
                "faithfulness": run.faithfulness,
                "answer_relevancy": run.answer_relevancy,
                "context_precision": run.context_precision,
                "context_recall": run.context_recall,
            },
            "per_question_breakdown": run.get_per_question(),
        }
    finally:
        db.close()


def compare_runs(run_id_1: str, run_id_2: str) -> dict:
    """
    Compare two evaluation runs side-by-side.

    Useful for comparing vector-only vs hybrid+rerank runs.

    Returns:
        Dict with both runs' scores and the delta between them.
    """
    card1 = get_scorecard(run_id_1)
    card2 = get_scorecard(run_id_2)

    if "error" in card1 or "error" in card2:
        return {"error": "One or both runs not found.", "run_1": card1, "run_2": card2}

    scores1 = card1["scores"]
    scores2 = card2["scores"]

    # Compute deltas
    delta = {}
    for metric in ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]:
        v1 = scores1.get(metric)
        v2 = scores2.get(metric)
        if v1 is not None and v2 is not None:
            delta[metric] = round(v2 - v1, 4)
        else:
            delta[metric] = None

    return {
        "run_1": {
            "run_id": run_id_1,
            "mode": card1["retrieval_mode"],
            "scores": scores1,
        },
        "run_2": {
            "run_id": run_id_2,
            "mode": card2["retrieval_mode"],
            "scores": scores2,
        },
        "delta": delta,
        "summary": _summarize_comparison(card1, card2, delta),
    }


def list_runs() -> list[dict]:
    """List all evaluation runs (summary view)."""
    SessionLocal = get_session_factory()
    db = SessionLocal()

    try:
        runs = db.query(EvalRun).order_by(EvalRun.timestamp.desc()).all()
        return [
            {
                "run_id": r.run_id,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                "retrieval_mode": r.retrieval_mode,
                "faithfulness": r.faithfulness,
                "answer_relevancy": r.answer_relevancy,
                "context_precision": r.context_precision,
                "context_recall": r.context_recall,
            }
            for r in runs
        ]
    finally:
        db.close()


def _summarize_comparison(card1: dict, card2: dict, delta: dict) -> str:
    """Generate a human-readable comparison summary."""
    lines = [
        f"Comparing: {card1['retrieval_mode']} (Run 1) vs {card2['retrieval_mode']} (Run 2)",
        "",
    ]

    for metric, d in delta.items():
        if d is not None:
            direction = "↑" if d > 0 else "↓" if d < 0 else "="
            lines.append(f"  {metric}: {direction} {abs(d):.4f}")
        else:
            lines.append(f"  {metric}: N/A")

    # Overall verdict
    improvements = sum(1 for d in delta.values() if d is not None and d > 0)
    regressions = sum(1 for d in delta.values() if d is not None and d < 0)

    if improvements > regressions:
        lines.append(f"\nVerdict: Run 2 ({card2['retrieval_mode']}) is better on {improvements}/{len(delta)} metrics.")
    elif regressions > improvements:
        lines.append(f"\nVerdict: Run 1 ({card1['retrieval_mode']}) is better on {regressions}/{len(delta)} metrics.")
    else:
        lines.append("\nVerdict: Results are mixed. Review per-question scores.")

    return "\n".join(lines)
