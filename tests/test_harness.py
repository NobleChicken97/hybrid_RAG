"""
Regression tests for the evaluation harness failure handling (2026-09-01 fix).

The first full eval run was poisoned: transient LLM API failures were stored
as the literal error string and RAGAS scored them as zeros, invalidating the
vector-only baseline. These tests lock in the fixed behavior:

  - failed generations are EXCLUDED from the RAGAS dataset / aggregate scores
  - they remain VISIBLE in the per-question breakdown with null scores
  - aggregate scores are computed over successfully generated questions only
"""

from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd
import pytest

from app.evaluation.harness import run_evaluation
from app.models import QAItem


def _qa(question: str) -> QAItem:
    return QAItem(question=question, ground_truth_answer="ground truth")


class _FakeRagasResult:
    """Stands in for ragas 0.4 EvaluationDataset with to_pandas()."""

    def __init__(self, df: pd.DataFrame):
        self._df = df

    def to_pandas(self) -> pd.DataFrame:
        return self._df


class _FakeSession:
    def __init__(self):
        self.added = []

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        pass

    def close(self):
        pass


class _FakeSessionFactory:
    def __init__(self):
        self.sessions = []

    def __call__(self):
        s = _FakeSession()
        self.sessions.append(s)
        return s


@pytest.fixture
def fake_settings():
    # Only attributes referenced by run_evaluation itself (the pipeline is
    # mocked; the 'none' judge backend skips RAGAS judge LLM construction).
    return SimpleNamespace(
        embedding_model="test-embed",
        reranker_model="test-rerank",
        retrieval_top_k=5,
        rerank_top_n=2,
        rrf_k=60,
        llm_backend="test",
        ragas_judge_backend="none",
        ragas_judge_model="test-judge",
    )


def test_failed_generation_excluded_from_aggregate(fake_settings):
    """A generation failure must not dilute aggregate scores with zeros."""
    scored_row = pd.DataFrame(
        {
            "faithfulness": [1.0],
            "answer_relevancy": [0.8],
            "context_precision": [0.6],
            "context_recall": [0.4],
        }
    )

    def fake_pipeline(question, mode="hybrid", top_k=5):
        if "boom" in question:
            raise RuntimeError("simulated cloud API failure")
        return "a good answer", ["context text"]

    factory = _FakeSessionFactory()

    with (
        patch("app.evaluation.harness._run_pipeline", side_effect=fake_pipeline),
        patch("app.evaluation.harness.get_settings", return_value=fake_settings),
        patch("app.evaluation.harness.get_session_factory", factory),
        patch("ragas.evaluate", return_value=_FakeRagasResult(scored_row)),
    ):
        run_id, agg, per_q = run_evaluation(
            [_qa("boom question"), _qa("good question")], mode="hybrid"
        )

    # Aggregate reflects only the scored (successful) question — faithfulness
    # would be 0.5 if the failed question leaked into the dataset as a zero.
    assert agg.faithfulness == 1.0
    assert agg.answer_relevancy == 0.8
    assert agg.context_precision == 0.6
    assert agg.context_recall == 0.4

    # Both questions stay visible in the breakdown.
    assert len(per_q) == 2
    failed = [p for p in per_q if p.answer.startswith("Error:")]
    ok = [p for p in per_q if not p.answer.startswith("Error:")]
    assert len(failed) == 1 and failed[0].question == "boom question"
    assert failed[0].faithfulness is None
    assert len(ok) == 1 and ok[0].answer == "a good answer"


def test_all_failed_skips_ragas(fake_settings):
    """When every generation fails, RAGAS is skipped and nothing is scored."""

    def always_fail(question, mode="hybrid", top_k=5):
        raise RuntimeError("cloud down")

    factory = _FakeSessionFactory()

    with (
        patch("app.evaluation.harness._run_pipeline", side_effect=always_fail),
        patch("app.evaluation.harness.get_settings", return_value=fake_settings),
        patch("app.evaluation.harness.get_session_factory", factory),
        patch("ragas.evaluate") as fake_eval,
    ):
        run_id, agg, per_q = run_evaluation([_qa("q1"), _qa("q2")], mode="hybrid")

    fake_eval.assert_not_called()
    assert agg.faithfulness is None
    assert len(per_q) == 2
    assert all(p.answer.startswith("Error:") for p in per_q)
