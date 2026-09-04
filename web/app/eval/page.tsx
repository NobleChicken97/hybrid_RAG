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
    <div className="rounded-lg border border-line bg-raised p-4">
      <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-dim">
        {label}
      </div>
      <div className="mt-1 font-display text-2xl font-semibold text-gold">
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

  const selectCls =
    "rounded-md border border-line bg-abyss px-2 py-1 text-ink outline-none focus:border-signal";

  return (
    <div className="flex flex-col gap-6">
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-signal">
          Prove
        </p>
        <h1 className="mt-1 font-display text-3xl font-semibold tracking-tight text-ink">
          Evaluation dashboard
        </h1>
      </div>

      <section className="flex flex-wrap items-end gap-3 rounded-xl border border-line bg-raised p-4">
        <label className="flex flex-col gap-1 text-sm text-mist">
          QA set
          <input
            value={qaSet}
            onChange={(e) => setQaSet(e.target.value)}
            className="rounded-md border border-line bg-abyss px-2 py-1 text-ink outline-none focus:border-signal"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm text-mist">
          Mode
          <select
            value={mode}
            onChange={(e) => setMode(e.target.value)}
            className={selectCls}
          >
            <option value="hybrid">hybrid</option>
            <option value="vector_only">vector_only</option>
          </select>
        </label>
        <button
          onClick={runEval}
          disabled={running}
          className="rounded-lg bg-signal px-4 py-1.5 text-sm font-semibold text-signal-ink transition hover:brightness-110 disabled:opacity-40"
        >
          {running ? "Running… (minutes)" : "Run evaluation"}
        </button>
      </section>

      {error && (
        <p className="rounded-lg border border-bad/50 bg-bad/10 p-3 text-sm text-ink">
          {error}
        </p>
      )}

      {latest && (
        <section className="flex flex-col gap-3">
          <h2 className="font-display text-lg font-semibold text-ink">
            <span className="font-mono text-sm font-medium text-good">
              {latest.run_id}
            </span>{" "}
            <span className="text-sm font-medium text-mist">
              ({latest.retrieval_mode})
            </span>
          </h2>
          <Scores scores={latest.scores} />
        </section>
      )}

      <section className="flex flex-col gap-3">
        <h2 className="font-display text-lg font-semibold text-ink">
          Past runs{" "}
          <span className="font-mono text-sm font-medium text-gold">
            ({runs.length})
          </span>
        </h2>
        <div className="overflow-x-auto rounded-xl border border-line bg-raised">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-line text-[11px] uppercase tracking-[0.14em] text-dim">
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
                <tr
                  key={r.run_id}
                  className="border-b border-line-soft text-mist last:border-0"
                >
                  <td className="px-3 py-2 font-mono text-xs text-ink">
                    {r.run_id}
                  </td>
                  <td className="px-3 py-2">{r.retrieval_mode}</td>
                  <td className="px-3 py-2 font-mono">
                    {r.scores.faithfulness?.toFixed(4) ?? "N/A"}
                  </td>
                  <td className="px-3 py-2 font-mono">
                    {r.scores.answer_relevancy?.toFixed(4) ?? "N/A"}
                  </td>
                  <td className="px-3 py-2 font-mono">
                    {r.scores.context_precision?.toFixed(4) ?? "N/A"}
                  </td>
                  <td className="px-3 py-2 font-mono">
                    {r.scores.context_recall?.toFixed(4) ?? "N/A"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {runs.length >= 2 && (
        <section className="flex flex-col gap-3 rounded-xl border border-line bg-raised p-4">
          <h2 className="font-display text-lg font-semibold text-ink">
            Compare two runs
          </h2>
          <div className="flex flex-wrap items-center gap-3 text-sm text-mist">
            <select
              value={run1}
              onChange={(e) => setRun1(e.target.value)}
              className={`${selectCls} font-mono text-xs`}
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
              className={`${selectCls} font-mono text-xs`}
            >
              {runs.map((r) => (
                <option key={r.run_id} value={r.run_id}>
                  {r.run_id} ({r.retrieval_mode})
                </option>
              ))}
            </select>
            <button
              onClick={compare}
              className="rounded-lg bg-signal px-4 py-1.5 text-sm font-semibold text-signal-ink transition hover:brightness-110"
            >
              Compare
            </button>
          </div>
          {comparison && "delta" in comparison && (
            <>
              <div className="grid grid-cols-4 gap-3 text-sm">
                {Object.entries(comparison.delta).map(([metric, d]) => (
                  <div
                    key={metric}
                    className="rounded-lg bg-abyss px-3 py-2"
                  >
                    <div className="text-xs capitalize text-dim">
                      {metric.replace("_", " ")}
                    </div>
                    <div
                      className={`font-mono font-semibold ${d == null ? "text-mist" : d > 0 ? "text-good" : d < 0 ? "text-bad" : "text-mist"}`}
                    >
                      {d == null
                        ? "N/A"
                        : `${d > 0 ? "↑" : d < 0 ? "↓" : "="} ${Math.abs(d).toFixed(4)}`}
                    </div>
                  </div>
                ))}
              </div>
              <pre className="whitespace-pre-wrap rounded-lg bg-abyss p-3 font-mono text-xs leading-5 text-mist">
                {comparison.summary}
              </pre>
            </>
          )}
        </section>
      )}
    </div>
  );
}
