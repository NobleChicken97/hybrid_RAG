"""Temporary script: run the full 20-question QA set through the eval harness
in both retrieval modes and dump aggregate results to eval_results.json."""
import sys
import json
import time

sys.stdout.reconfigure(encoding="utf-8")

from app.evaluation.qa_loader import load_qa_set
from app.evaluation.harness import run_evaluation

qa_items = load_qa_set("default")
print(f"[FullEval] Loaded {len(qa_items)} QA items")

results = {}
for mode in ("hybrid", "vector_only"):
    t0 = time.time()
    run_id, agg, per_q = run_evaluation(qa_items, mode=mode)
    results[mode] = {
        "run_id": run_id,
        "elapsed_s": round(time.time() - t0, 1),
        "scores": agg.model_dump(),
        "per_question": [q.model_dump() for q in per_q],
    }
    with open("eval_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"[FullEval] {mode} done in {results[mode]['elapsed_s']}s -> {run_id}")

print("[FullEval] ALL DONE")
print(json.dumps({m: r["scores"] for m, r in results.items()}, indent=2))
