"""Shared-secret guard on POST /eval/run (EVAL_TOKEN).

EVAL_TOKEN empty (dev default) -> open. Set -> the matching `x-eval-token`
header is required, else 403. run_evaluation is mocked: no LLM calls and no
model loads, so these tests stay light.
"""

import asyncio

import pytest
from fastapi.testclient import TestClient

from app import config as config_module
from app.api import eval as eval_module
from app.main import app

SCORES = {
    "faithfulness": 1.0,
    "answer_relevancy": 1.0,
    "context_precision": 1.0,
    "context_recall": 1.0,
}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def _mock_run(monkeypatch):
    monkeypatch.setattr(
        eval_module,
        "run_evaluation",
        lambda *a, **kw: ("eval_test", dict(SCORES), []),
    )


@pytest.fixture()
def _locked(monkeypatch):
    """EVAL_TOKEN set: settings cache must be rebuilt to see it, and again
    afterwards so no state leaks into other tests."""
    monkeypatch.setenv("EVAL_TOKEN", "test-secret")
    config_module.get_settings.cache_clear()
    yield
    config_module.get_settings.cache_clear()


@pytest.fixture()
def _open(monkeypatch):
    monkeypatch.delenv("EVAL_TOKEN", raising=False)
    config_module.get_settings.cache_clear()
    yield
    config_module.get_settings.cache_clear()


def _run(client: TestClient, token: str | None = None):
    headers = {"x-eval-token": token} if token else {}
    return client.post(
        "/eval/run",
        json={"qa_set_name": "default", "mode": "hybrid"},
        headers=headers,
    )


def test_eval_run_open_without_token(client: TestClient, _open, _mock_run):
    resp = _run(client)
    assert resp.status_code == 200, resp.text
    assert resp.json()["run_id"] == "eval_test"


def test_eval_run_locked_no_header(client: TestClient, _locked, _mock_run):
    resp = _run(client)
    assert resp.status_code == 403
    assert "x-eval-token" in resp.json()["detail"]


def test_eval_run_locked_wrong_token(client: TestClient, _locked, _mock_run):
    resp = _run(client, token="nope")
    assert resp.status_code == 403


def test_eval_run_locked_correct_token(client: TestClient, _locked, _mock_run):
    resp = _run(client, token="test-secret")
    assert resp.status_code == 200, resp.text
    assert resp.json()["run_id"] == "eval_test"


def test_eval_run_offloads_event_loop(client: TestClient, _open, monkeypatch):
    """run_evaluation must not execute on the event-loop thread.

    Regression test for prod run eval_963a9e98: RAGAS executes nested async
    code, which crashes on a running loop (uvloop). The endpoint must offload
    to a worker thread, where no loop is running — exactly like the local
    script runs that always worked.
    """
    seen = {}

    def fake_run(*a, **kw):
        try:
            asyncio.get_running_loop()
            seen["loop"] = True
        except RuntimeError:
            seen["loop"] = False
        return ("eval_test", dict(SCORES), [])

    monkeypatch.setattr(eval_module, "run_evaluation", fake_run)
    resp = _run(client)
    assert resp.status_code == 200, resp.text
    assert seen.get("loop") is False, "run_evaluation ran on the event-loop thread"
