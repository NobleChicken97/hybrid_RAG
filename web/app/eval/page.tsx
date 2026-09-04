"use client";

import { useEffect, useState } from "react";
import {
  api,
  type EvalRunResponse,
  type EvalRunSummary,
  type EvalScores,
} from "@/lib/api";

function ScoreRow({ label, value }: { label: string; value: number | null }) {
  return (
    <div className="rounded-lg border border-zinc-200 bg-white p-3">
      <div className="text-xs uppercase tracking-wide text-zinc-500">
        {label}
      </div>
      <div className="mt-1 text-xl font-semibold">
        {value == null ? "N/A" : value.toFixed(4)}
      </div>
    </div>
  );
}

function Scores({ scores }: { scores: EvalScores }) {
  return (
    <div className="grid grid-cols-4 gap-3">
      <ScoreRow label="Faithfulness" value={scores.faithfulness} />
      <ScoreRow label="Answer relevancy" value={scores.answer_relevancy} />
      <ScoreRow label="Context precision" value={scores.context_precision} />
      <ScoreRow label="Context recall" value={scores.context_recall} />
    </div>
  );
}

export default function EvalPage() {
  const [qaSet, setQaSet] = useState("default");
  const [mode, setMode] = useState("hybrid");
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [latest, setLatest] = useState<EvalRunResponse | null>(null);
  const [runs, setRuns] = useState<EvalRunSummary[]>([]);
  const [run1, setRun1] = useState("");
  const [run2, setRun2] = useState("");
  const [comparison, setComparison] = useState<Record<string, never> | {
    run_1: { mode: string; scores: EvalScores };
    run_2: { mode: string; scores: EvalScores };
    delta: Record<string, number | null>;
    summary: string;
  } | null>(null);

  async function refreshRuns() {
    try {
      const list = await api.evalRuns();
      setRuns(list);
      if (!run1 && list.length > 0) setRun1(list[0].run_id);
      if (!run2 && list.length > 1) setRun2(list[1].run_id);
    } catch {
      // Backend may be down; the health banner on Overview covers it.
    }
  }

  useEffect(() => {
    let cancelled = false;
    // Async callback (not a synchronous setState): fetches past runs once.
    api
      .evalRuns()
      .then((list) => {
        if (cancelled) return;
        setRuns(list);
        setRun1((prev) => prev || list[0]?.run_id || "");
        setRun2((prev) => prev || list[1]?.run_id || "");
      })
      .catch(() => {
        // Backend may be down; the health banner on Overview covers it.
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function runEval() {
    setRunning(true);
    setError(null);
    setLatest(null);
    try {
      const res = await api.evalRun(qaSet, mode);
      setLatest(res);
      await refreshRuns();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(false);
    }
  }

  async function compare() {
    setError(null);
    try {
      setComparison(
        (await api.compare(run1, run2)) as Exclude<typeof comparison, null>,
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold tracking-tight">
        📊 Evaluation dashboard
      </h1>

      <section className="flex items-end gap-3 rounded-xl border border-zinc-200 bg-white p-4">
        <label className="flex flex-col gap-1 text-sm">
          QA set
          <input
            value={qaSet}
            onChange={(e) => setQaSet(e.target.value)}
            className="rounded border border-zinc-300 px-2 py-1"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Mode
          <select
            value={mode}
            onChange={(e) => setMode(e.target.value)}
            className="rounded border border-zinc-300 px-2 py-1"
          >
            <option value="hybrid">hybrid</option>
            <option value="vector_only">vector_only</option>
          </select>
        </label>
        <button
          onClick={runEval}
          disabled={running}
          className="rounded-lg bg-zinc-900 px-4 py-1.5 text-sm font-medium text-white disabled:opacity-40"
        >
          {running ? "Running… (minutes)" : "▶️ Run evaluation"}
        </button>
      </section>

      {error && (
        <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </p>
      )}

      {latest && (
        <section className="flex flex-col gap-3">
          <h2 className="font-medium">
            ✅ {latest.run_id} ({latest.retrieval_mode})
          </h2>
          <Scores scores={latest.scores} />
        </section>
      )}

      <section className="flex flex-col gap-3">
        <h2 className="font-medium">📜 Past runs ({runs.length})</h2>
        <div className="overflow-x-auto rounded-xl border border-zinc-200 bg-white">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-zinc-200 text-xs uppercase text-zinc-500">
                <th className="px-3 py-2">Run</th>
                <th className="px-3 py-2">Mode</th>
                <th className="px-3 py-2">Faith.</th>
                <th className="px-3 py-2">Rel.</th>
                <th className="px-3 py-2">Prec.</th>
                <th className="px-3 py-2">Recall</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((r) => (
                <tr key={r.run_id} className="border-b border-zinc-100">
                  <td className="px-3 py-2 font-mono text-xs">{r.run_id}</td>
                  <td className="px-3 py-2">{r.retrieval_mode}</td>
                  <td className="px-3 py-2">
                    {r.scores.faithfulness?.toFixed(4) ?? "N/A"}
                  </td>
                  <td className="px-3 py-2">
                    {r.scores.answer_relevancy?.toFixed(4) ?? "N/A"}
                  </td>
                  <td className="px-3 py-2">
                    {r.scores.context_precision?.toFixed(4) ?? "N/A"}
                  </td>
                  <td className="px-3 py-2">
                    {r.scores.context_recall?.toFixed(4) ?? "N/A"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {runs.length >= 2 && (
        <section className="flex flex-col gap-3 rounded-xl border border-zinc-200 bg-white p-4">
          <h2 className="font-medium">🔄 Compare two runs</h2>
          <div className="flex items-center gap-3 text-sm">
            <select
              value={run1}
              onChange={(e) => setRun1(e.target.value)}
              className="rounded border border-zinc-300 px-2 py-1 font-mono text-xs"
            >
              {runs.map((r) => (
                <option key={r.run_id} value={r.run_id}>
                  {r.run_id} ({r.retrieval_mode})
                </option>
              ))}
            </select>
            <span>vs</span>
            <select
              value={run2}
              onChange={(e) => setRun2(e.target.value)}
              className="rounded border border-zinc-300 px-2 py-1 font-mono text-xs"
            >
              {runs.map((r) => (
                <option key={r.run_id} value={r.run_id}>
                  {r.run_id} ({r.retrieval_mode})
                </option>
              ))}
            </select>
            <button
              onClick={compare}
              className="rounded-lg bg-zinc-900 px-4 py-1.5 text-sm font-medium text-white"
            >
              📊 Compare
            </button>
          </div>
          {comparison && "delta" in comparison && (
            <>
              <div className="grid grid-cols-4 gap-3 text-sm">
                {Object.entries(comparison.delta).map(([metric, d]) => (
                  <div
                    key={metric}
                    className="rounded-lg bg-zinc-50 px-3 py-2"
                  >
                    <div className="text-xs capitalize text-zinc-500">
                      {metric.replace("_", " ")}
                    </div>
                    <div className="font-semibold">
                      {d == null
                        ? "N/A"
                        : `${d > 0 ? "↑" : d < 0 ? "↓" : "="} ${Math.abs(d).toFixed(4)}`}
                    </div>
                  </div>
                ))}
              </div>
              <pre className="whitespace-pre-wrap rounded-lg bg-zinc-950 p-3 text-xs text-zinc-100">
                {comparison.summary}
              </pre>
            </>
          )}
        </section>
      )}
    </div>
  );
}
