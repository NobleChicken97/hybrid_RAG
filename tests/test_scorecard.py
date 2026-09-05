"""Scorecard contract tests — locks the shapes the web UI depends on.

Regression cover for two real bugs caught by the 2026-09-05 live probe:
`GET /eval/runs/{id}` returned `aggregate_scores` while every other
endpoint uses `scores`, and `compare_runs` never executed (its assignments
were dead code inside the error branch → 500 on valid IDs).
Seeds run rows into the isolated test DB (see tests/conftest.py).
"""

from app.database import EvalRun, get_session_factory, init_db
from app.evaluation.scorecard import compare_runs, get_scorecard


def _seed():
    init_db()
    session = get_session_factory()()
    try:
        for rid, faith in (("eval_test_a", 0.9), ("eval_test_b", 0.8)):
            if not session.query(EvalRun).filter_by(run_id=rid).first():
                session.add(
                    EvalRun(
                        run_id=rid,
                        retrieval_mode="hybrid",
                        faithfulness=faith,
                        answer_relevancy=0.9,
                        context_precision=0.9,
                        context_recall=1.0,
                    )
                )
        session.commit()
    finally:
        session.close()


def test_scorecard_uses_scores_key():
    _seed()
    card = get_scorecard("eval_test_a")
    assert set(card["scores"]) == {
        "faithfulness",
        "answer_relevancy",
        "context_precision",
        "context_recall",
    }, "detail shape must match EvalRunSummary.scores"
    assert card["scores"]["faithfulness"] == 0.9


def test_compare_runs_scores_and_delta():
    _seed()
    out = compare_runs("eval_test_a", "eval_test_b")
    assert "error" not in out
    assert out["run_1"]["scores"]["faithfulness"] == 0.9
    assert out["delta"]["faithfulness"] == round(0.8 - 0.9, 4)


def test_compare_runs_bad_ids_no_crash():
    out = compare_runs("nope", "nope2")
    assert "error" in out
