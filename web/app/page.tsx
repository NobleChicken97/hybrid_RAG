"use client";

import { Button } from "@/components/ui/button";
import { PipelineDiagram } from "@/components/pipeline-diagram";
import { Reveal } from "@/components/reveal";
import { Ticker } from "@/components/ticker";
import Link from "next/link";
import { useEffect, useState } from "react";
import {
  api,
  type DocumentInfo,
  type EvalRunSummary,
  type Health,
} from "@/lib/api";

const DRAWERS = [
  {
    href: "/ingest",
    step: "STEP 01",
    title: "Ingest",
    body: "Shelve PDF, Markdown, or text. Context-aware chunking preserves document structure.",
  },
  {
    href: "/ask",
    step: "STEP 02",
    title: "Ask",
    body: "Receive an evidence slip: a cited answer with the full retrieval ledger.",
  },
  {
    href: "/eval",
    step: "STEP 03",
    title: "Evaluate",
    body: "Audit runs in the ledger: RAGAS scorecards, hybrid against vector-only.",
  },
];

function Meter({
  label,
  value,
  max,
  suffix,
}: {
  label: string;
  value: number;
  max: number;
  suffix: string;
}) {
  const [on, setOn] = useState(false);
  useEffect(() => {
    const r = requestAnimationFrame(() => setOn(true));
    return () => cancelAnimationFrame(r);
  }, []);
  const pct = max > 0 ? Math.round((value / max) * 100) : 0;
  return (
    <div>
      <div className="flex items-baseline justify-between gap-2">
        <span className="truncate text-sm font-semibold text-ink">
          {label}
        </span>
        <span className="font-mono text-xs tabular-nums text-mist">
          {value} {suffix}
        </span>
      </div>
      <div className="mt-1 h-2 w-full bg-ink/10">
        <div
          className="h-2 bg-signal transition-[width] duration-700 ease-out"
          style={{ width: on ? `${pct}%` : "0%" }}
        />
      </div>
    </div>
  );
}

export default function Home() {
  const [health, setHealth] = useState<Health | null>(null);
  const [docs, setDocs] = useState<DocumentInfo[]>([]);
  const [runs, setRuns] = useState<EvalRunSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .health()
      .then(setHealth)
      .catch((e: Error) => setError(e.message));
    api.documents().then(setDocs).catch(() => {});
    api.evalRuns().then(setRuns).catch(() => {});
  }, []);

  const maxChunks = Math.max(1, ...docs.map((d) => d.chunk_count));
  const latest = runs[0];
  const fmt2 = (v: number | null) => (v == null ? "—" : v.toFixed(2));
  const tickerItems = runs.map((r) => ({
    top: `${r.run_id} · ${r.retrieval_mode}`,
    bottom: `faith ${fmt2(r.scores.faithfulness)} · rel ${fmt2(r.scores.answer_relevancy)} · prec ${fmt2(r.scores.context_precision)} · rec ${fmt2(r.scores.context_recall)}`,
  }));

  const MARQUEE = [
    "BM25",
    "VECTOR SEARCH",
    "RRF FUSION",
    "CROSS-ENCODER RERANK",
    "TOP-20 POOL",
    "TOP-5 CUT",
    "COMPRESSION",
    "CITATIONS",
    "RAGAS FAITHFULNESS",
    "EVIDENCE SLIPS",
  ];

  return (
    <div className="flex flex-col gap-px border border-line bg-line">
      <div className="bg-abyss p-6 sm:p-10">
        <div className="grid gap-8 xl:grid-cols-12">
          <div className="xl:col-span-7">
            <h1 className="font-display text-6xl font-bold uppercase leading-[0.95] tracking-tight text-ink sm:text-8xl">
              Every claim
              <br />
              has a call number.
            </h1>
            <p className="mt-4 max-w-xl leading-6 text-mist">
              A production-grade retrieval-augmented generation pipeline
              with hybrid retrieval, cross-encoder reranking, context
              compression, and RAGAS evaluation. Nothing here answers from
              memory — everything is shelved, cited, and auditable.
            </p>
            <div className="mt-5 flex flex-wrap gap-3">
              <Link href="/ask">
                <Button className="font-mono text-xs font-bold uppercase tracking-[0.18em]">
                  Ask the stacks →
                </Button>
              </Link>
              <Link href="/ingest">
                <Button
                  variant="outline"
                  className="font-mono text-xs font-bold uppercase tracking-[0.18em]"
                >
                  Shelve a document
                </Button>
              </Link>
            </div>
            {health && (
              <p className="mt-4 font-mono text-[11px] uppercase tracking-[0.2em] text-mist">
                Environment <span className="text-ink">{health.environment}</span>
                {"  ·  "}LLM backend{" "}
                <span className="text-ink">{health.llm_backend}</span>
              </p>
            )}
          </div>
          <div className="flex flex-col gap-px border border-line bg-line xl:col-span-5">
            <div className="bg-panel px-5 py-3 font-mono text-[11px] font-bold uppercase tracking-[0.24em] text-signal">
              Reading-room index
            </div>
            <div className="flex flex-1 flex-col justify-center gap-4 bg-panel p-5">
              <div className="flex items-baseline justify-between border-b border-line-soft pb-3">
                <span className="text-sm font-semibold uppercase tracking-[0.14em] text-mist">
                  Retrieval
                </span>
                <span className="font-mono text-xs text-ink">
                  BM25 + vector · RRF
                </span>
              </div>
              <div className="flex items-baseline justify-between border-b border-line-soft pb-3">
                <span className="text-sm font-semibold uppercase tracking-[0.14em] text-mist">
                  Reranker
                </span>
                <span className="font-mono text-xs text-ink">
                  bge-base · top 5
                </span>
              </div>
              <div className="flex items-baseline justify-between border-b border-line-soft pb-3">
                <span className="text-sm font-semibold uppercase tracking-[0.14em] text-mist">
                  Embeddings
                </span>
                <span className="font-mono text-xs text-ink">
                  bge-small · 384d
                </span>
              </div>
              <div className="flex items-baseline justify-between border-b border-line-soft pb-3">
                <span className="text-sm font-semibold uppercase tracking-[0.14em] text-mist">
                  Judge
                </span>
                <span className="font-mono text-xs text-ink">
                  RAGAS · 4 metrics
                </span>
              </div>
              <div className="flex items-baseline justify-between border-b border-line-soft pb-3">
                <span className="text-sm font-semibold uppercase tracking-[0.14em] text-mist">
                  Compression
                </span>
                <span className="font-mono text-xs text-ink">
                  budget · 2000 tok
                </span>
              </div>
              <div className="flex items-baseline justify-between">
                <span className="text-sm font-semibold uppercase tracking-[0.14em] text-mist">
                  Corpus
                </span>
                <span className="font-mono text-xs text-ink">
                  {health ? `${health.documents_count} docs` : "…"}
                </span>
              </div>
            </div>
          </div>
        </div>
        <Reveal className="mt-6 border border-line bg-graph bg-panel p-4">
          <PipelineDiagram />
        </Reveal>
      </div>

      <div
        aria-hidden="true"
        className="overflow-hidden border-y-2 border-signal bg-signal py-2"
      >
        <div className="marquee-track flex w-max whitespace-nowrap">
          {[...MARQUEE, ...MARQUEE].map((w, i) => (
            <span
              key={i}
              className="px-6 font-mono text-[11px] font-bold uppercase tracking-[0.24em] text-signal-ink"
            >
              {w} <span className="opacity-60">{"///"}</span>
            </span>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-3 divide-x divide-console-line bg-console">
        {(
          [
            ["Documents shelved", health?.documents_count],
            ["Chunks indexed", health?.chunks_count],
            ["Audits on record", health?.eval_runs_count],
          ] as [string, number | undefined][]
        ).map(([label, value]) => (
          <div key={label} className="p-6">
            <div className="font-mono text-[11px] font-semibold uppercase tracking-[0.2em] text-console-mist">
              {label}
            </div>
            <div className="mt-1 font-display text-6xl font-bold tabular-nums text-console-ink">
              {value ?? (error ? "—" : "…")}
            </div>
          </div>
        ))}
      </div>
      {error && (
        <p className="border-y border-bad bg-bad/10 p-5 text-sm text-ink">
          The stacks are unreachable: {error}. Start the backend with{" "}
          <code className="font-mono text-mist">
            uvicorn app.main:app --port 8000
          </code>
          .
        </p>
      )}

      <Ticker items={tickerItems} />

      <div className="grid gap-px bg-line lg:grid-cols-2">
        <Reveal className="bg-panel p-6">
          <div className="flex items-baseline justify-between">
            <h2 className="font-display text-2xl font-bold uppercase text-ink">
              On the shelves
            </h2>
            <Link
              href="/system"
              className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-signal hover:underline"
            >
              Full inventory →
            </Link>
          </div>
          <div className="mt-4 flex flex-col gap-4">
            {docs.length === 0 && (
              <p className="text-sm text-mist">
                {error ? "Cannot reach the backend." : "Loading holdings…"}
              </p>
            )}
            {docs.map((d) => (
              <Meter
                key={d.doc_id}
                label={d.title}
                value={d.chunk_count}
                max={maxChunks}
                suffix="chunks"
              />
            ))}
          </div>
        </Reveal>
        <Reveal className="bg-panel p-6" delay={120}>
          <div className="flex items-baseline justify-between">
            <h2 className="font-display text-2xl font-bold uppercase text-ink">
              Latest audit
            </h2>
            <Link
              href="/eval"
              className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-signal hover:underline"
            >
              Audit ledger →
            </Link>
          </div>
          {!latest ? (
            <p className="mt-4 text-sm leading-6 text-mist">
              No audits on record yet. Run the holdings against the question
              set to file the first slip.
            </p>
          ) : (
            <div className="mt-4 flex flex-col gap-4">
              <p className="font-mono text-[11px] uppercase tracking-[0.16em] text-mist">
                {latest.run_id} · {latest.retrieval_mode}
              </p>
              {(
                [
                  ["Faithfulness", latest.scores.faithfulness],
                  ["Answer relevancy", latest.scores.answer_relevancy],
                  ["Context precision", latest.scores.context_precision],
                  ["Context recall", latest.scores.context_recall],
                ] as [string, number | null][]
              ).map(([label, v]) => (
                <Meter
                  key={label}
                  label={label}
                  value={v ?? 0}
                  max={1}
                  suffix={v == null ? "N/A" : v.toFixed(2)}
                />
              ))}
            </div>
          )}
        </Reveal>
      </div>

      <div className="grid gap-px bg-line sm:grid-cols-3">
        {DRAWERS.map((card) => (
          <Link
            key={card.href}
            href={card.href}
            className="group flex flex-col bg-raised p-6 transition-colors hover:bg-hover"
          >
            <div className="inline-block self-start bg-signal px-2 py-0.5 font-mono text-[11px] font-bold uppercase tracking-[0.2em] text-signal-ink">
              {card.step}
            </div>
            <div className="mt-3 font-display text-4xl font-bold uppercase text-ink">
              {card.title}
            </div>
            <p className="mt-2 flex-1 text-sm leading-6 text-mist">
              {card.body}
            </p>
            <div className="mt-4">
              <Button className="font-mono text-[11px] font-bold uppercase tracking-[0.2em]">
                Open the drawer →
              </Button>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
