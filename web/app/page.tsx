"use client";

import { Button } from "@/components/ui/button";
import { PipelineDiagram } from "@/components/pipeline-diagram";
import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type Health } from "@/lib/api";

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

export default function Home() {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .health()
      .then(setHealth)
      .catch((e: Error) => setError(e.message));
  }, []);

  return (
    <div className="flex flex-col gap-px border border-line bg-line">
      <div className="bg-abyss p-6 sm:p-10">
        <p className="font-mono text-xs font-semibold uppercase tracking-[0.28em] text-signal">
          A retrieval console · EST. holdings verified nightly
        </p>
        <h1 className="mt-3 font-display text-6xl font-bold uppercase leading-[0.95] tracking-tight text-ink sm:text-8xl">
          Every claim
          <br />
          has a call number.
        </h1>
        <p className="mt-4 max-w-xl leading-6 text-mist">
          A production-grade retrieval-augmented generation pipeline with
          hybrid retrieval, cross-encoder reranking, context compression, and
          RAGAS evaluation. Nothing here answers from memory — everything is
          shelved, cited, and auditable.
        </p>
        <div className="mt-6 border border-line bg-panel p-4">
          <PipelineDiagram />
        </div>
        {health && (
          <p className="mt-4 font-mono text-[11px] uppercase tracking-[0.2em] text-mist">
            Environment <span className="text-ink">{health.environment}</span>
            {"  ·  "}LLM backend{" "}
            <span className="text-ink">{health.llm_backend}</span>
          </p>
        )}
      </div>

      <div className="grid grid-cols-3 divide-x divide-console-line bg-console">
        {(
          [
            ["Documents shelved", health?.documents_count],
            ["Chunks indexed", health?.chunks_count],
            ["Audits on record", health?.eval_runs_count],
          ] as [string, number | undefined][]
        ).map(([label, value]) => (
          <div key={label} className="bg-console p-6">
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

      <div className="grid grid-cols-3 gap-px bg-line">
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
