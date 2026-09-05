"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useEffect, useState } from "react";
import {
  api,
  type EvalRunResponse,
  type EvalRunSummary,
  type EvalScores,
} from "@/lib/api";

function ScoreRow({ label, value }: { label: string; value: number | null }) {
  return (
    <div className="bg-panel p-4">
      <div className="font-mono text-[11px] font-semibold uppercase tracking-[0.2em] text-dim">
        {label}
      </div>
      <div className="mt-1 font-display text-3xl font-extrabold tabular-nums text-gold">
        {value == null ? "N/A" : value.toFixed(4)}
      </div>
    </div>
  );
}

function Scores({ scores }: { scores: EvalScores }) {
  return (
    <div className="grid grid-cols-4 gap-px border border-line bg-line">
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
    "border border-line bg-abyss px-2 py-1 text-ink outline-none focus:border-signal";

  return (
    <div className="flex flex-col gap-px border border-line bg-line">
      <div className="bg-panel p-5">
        <p className="font-mono text-[11px] font-semibold uppercase tracking-[0.24em] text-signal">
          03 / Prove
        </p>
        <h1 className="mt-1 font-display text-3xl font-extrabold uppercase tracking-tight text-ink">
          Evaluation dashboard
        </h1>
      </div>

      <section className="flex flex-wrap items-end gap-3 bg-panel p-5">
        <label className="flex flex-col gap-1 font-mono text-[11px] uppercase tracking-[0.18em] text-mist">
          QA set
          <Input
            value={qaSet}
            onChange={(e) => setQaSet(e.target.value)}
            className="rounded-none border-line bg-abyss text-sm normal-case tracking-normal text-ink focus-visible:ring-signal"
          />
        </label>
        <label className="flex flex-col gap-1 font-mono text-[11px] uppercase tracking-[0.18em] text-mist">
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
        <Button
          onClick={runEval}
          disabled={running}
          className="rounded-none font-mono text-xs font-bold uppercase tracking-[0.18em]"
        >
          {running ? "Running… (minutes)" : "Run evaluation"}
        </Button>
      </section>

      {error && (
        <p className="border-y border-bad bg-bad/10 p-4 text-sm text-ink">
          <span className="font-mono text-[11px] font-semibold uppercase tracking-[0.2em] text-bad">
            Error
          </span>
          <br />
          {error}
        </p>
      )}

      {latest && (
        <section className="flex flex-col gap-px bg-line-soft">
          <h2 className="bg-panel px-5 pb-1 pt-4 font-mono text-sm font-semibold text-good">
            {latest.run_id}{" "}
            <span className="text-xs font-medium text-mist">
              ({latest.retrieval_mode})
            </span>
          </h2>
          <Scores scores={latest.scores} />
        </section>
      )}

      <section className="flex flex-col bg-panel">
        <h2 className="px-5 pb-1 pt-4 font-display text-lg font-extrabold uppercase text-ink">
          Past runs{" "}
          <span className="font-mono text-sm font-semibold text-gold">
            [{runs.length}]
          </span>
        </h2>
        <div className="overflow-x-auto p-5 pt-2">
          <Table className="border border-line-soft font-mono text-xs">
            <TableHeader className="bg-raised">
              <TableRow className="border-b border-line hover:bg-transparent">
                <TableHead className="text-dim">RUN</TableHead>
                <TableHead className="text-dim">MODE</TableHead>
                <TableHead className="text-dim">FAITH.</TableHead>
                <TableHead className="text-dim">REL.</TableHead>
                <TableHead className="text-dim">PREC.</TableHead>
                <TableHead className="text-dim">RECALL</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {runs.map((r) => (
                <TableRow
                  key={r.run_id}
                  className="border-b border-line-soft text-mist last:border-0 hover:bg-hover"
                >
                  <TableCell className="text-ink">{r.run_id}</TableCell>
                  <TableCell>{r.retrieval_mode}</TableCell>
                  <TableCell className="tabular-nums">
                    {r.scores.faithfulness?.toFixed(4) ?? "N/A"}
                  </TableCell>
                  <TableCell className="tabular-nums">
                    {r.scores.answer_relevancy?.toFixed(4) ?? "N/A"}
                  </TableCell>
                  <TableCell className="tabular-nums">
                    {r.scores.context_precision?.toFixed(4) ?? "N/A"}
                  </TableCell>
                  <TableCell className="tabular-nums">
                    {r.scores.context_recall?.toFixed(4) ?? "N/A"}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </section>

      {runs.length >= 2 && (
        <section className="flex flex-col gap-3 bg-panel p-5">
          <h2 className="font-display text-lg font-extrabold uppercase text-ink">
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
            <span className="font-mono text-[11px] text-dim">VS</span>
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
            <Button
              onClick={compare}
              className="rounded-none font-mono text-xs font-bold uppercase tracking-[0.18em]"
            >
              Compare
            </Button>
          </div>
          {comparison && "delta" in comparison && (
            <>
              <div className="grid grid-cols-4 gap-px border border-line bg-line text-sm">
                {Object.entries(comparison.delta).map(([metric, d]) => (
                  <div key={metric} className="bg-abyss px-3 py-2">
                    <div className="font-mono text-[11px] uppercase tracking-[0.16em] text-dim">
                      {metric.replace("_", " ")}
                    </div>
                    <div
                      className={`font-mono font-bold tabular-nums ${d == null ? "text-mist" : d > 0 ? "text-good" : d < 0 ? "text-bad" : "text-mist"}`}
                    >
                      {d == null
                        ? "N/A"
                        : `${d > 0 ? "+" : d < 0 ? "-" : "="} ${Math.abs(d).toFixed(4)}`}
                    </div>
                  </div>
                ))}
              </div>
              <pre className="whitespace-pre-wrap border border-line-soft bg-abyss p-3 font-mono text-xs leading-5 text-mist">
                {comparison.summary}
              </pre>
            </>
          )}
        </section>
      )}
    </div>
  );
}
