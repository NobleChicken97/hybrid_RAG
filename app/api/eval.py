"""
Evaluation API endpoints.

POST /eval/run   — Trigger a new evaluation run
GET  /eval/runs  — List all evaluation runs
GET  /eval/runs/{run_id}  — Get a specific run's scorecard
POST /eval/compare — Compare two runs side-by-side
"""

from fastapi import APIRouter, HTTPException

from app.models import EvalRunRequest, EvalRunResponse, EvalRunSummary, EvalScores
from app.evaluation.qa_loader import load_qa_set, list_qa_sets
from app.evaluation.harness import run_evaluation
from app.evaluation.scorecard import get_scorecard, compare_runs, list_runs

router = APIRouter(prefix="/eval", tags=["Evaluation"])


@router.post("/run", response_model=EvalRunResponse)
async def trigger_eval_run(request: EvalRunRequest):
    """
    Trigger a new evaluation run.

    Either provide a qa_set_name (loads from data/qa_sets/) or
    inline qa_items in the request body.
    """
    # Load QA items
    if request.qa_items:
        qa_items = request.qa_items
    else:
        try:
            qa_items = load_qa_set(request.qa_set_name)
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))

    if not qa_items:
        raise HTTPException(status_code=400, detail="QA set is empty.")

    # Run evaluation
    run_id, scores, per_question = run_evaluation(qa_items, mode=request.mode)

    return EvalRunResponse(
        run_id=run_id,
        retrieval_mode=request.mode,
        timestamp=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        scores=scores,
        per_question_breakdown=per_question,
    )


@router.get("/runs", response_model=list[EvalRunSummary])
async def get_eval_runs():
    """List all evaluation runs."""
    runs = list_runs()
    return [
        EvalRunSummary(
            run_id=r["run_id"],
            retrieval_mode=r["retrieval_mode"],
            timestamp=r["timestamp"],
            scores=EvalScores(
                faithfulness=r.get("faithfulness"),
                answer_relevancy=r.get("answer_relevancy"),
                context_precision=r.get("context_precision"),
                context_recall=r.get("context_recall"),
            ),
        )
        for r in runs
    ]


@router.get("/runs/{run_id}")
async def get_eval_run(run_id: str):
    """Get the full scorecard for a specific evaluation run."""
    scorecard = get_scorecard(run_id)
    if "error" in scorecard:
        raise HTTPException(status_code=404, detail=scorecard["error"])
    return scorecard


@router.post("/compare")
async def compare_eval_runs(run_id_1: str, run_id_2: str):
    """Compare two evaluation runs side-by-side."""
    result = compare_runs(run_id_1, run_id_2)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/qa-sets")
async def get_qa_sets():
    """List available QA evaluation sets."""
    return {"qa_sets": list_qa_sets()}
