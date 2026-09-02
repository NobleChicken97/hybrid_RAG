"""Run ONLY the vector_only eval mode and merge it into eval_results.json.

Use after the Gemini daily quota reset (midnight Pacific) — the hybrid run
eval_dc701f3b is already complete and clean; re-running it would waste quota.

Probes the API first: if the quota is still exhausted, exits without running.
"""
import json
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

from app.config import get_settings
from app.generation.llm import generate


def quota_available() -> bool:
    try:
        generate("Reply with exactly: OK", max_tokens=10)
        return True
    except Exception as e:
        print(f"[VecEval] Quota probe failed: {e}")
        return False


def main() -> None:
    settings = get_settings()
    print(f"[VecEval] Generation backend: {settings.llm_backend} ({settings.gemini_model})")

    if not quota_available():
        print("[VecEval] API quota still exhausted — aborting without wasting calls.")
        sys.exit(2)

    from app.evaluation.harness import run_evaluation
    from app.evaluation.qa_loader import load_qa_set

    qa_items = load_qa_set("default")
    print(f"[VecEval] Loaded {len(qa_items)} QA items")

    with open("eval_results.json", encoding="utf-8") as f:
        results = json.load(f)

    t0 = time.time()
    run_id, agg, per_q = run_evaluation(qa_items, mode="vector_only")
    results["vector_only"] = {
        "run_id": run_id,
        "elapsed_s": round(time.time() - t0, 1),
        "scores": agg.model_dump(),
        "per_question": [q.model_dump() for q in per_q],
    }
    with open("eval_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    fails = sum(1 for q in per_q if q.answer.startswith("Error:"))
    print(f"[VecEval] done in {results['vector_only']['elapsed_s']}s -> {run_id} (failed: {fails})")
    print(json.dumps(agg.model_dump(), indent=2))


if __name__ == "__main__":
    main()
