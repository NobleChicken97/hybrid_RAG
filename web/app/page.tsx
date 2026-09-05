"use client";

import { Button } from "@/components/ui/button";
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
      <div className="bg-panel p-6">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <h1 className="font-display text-5xl font-bold tracking-tight text-ink">
            Hybrid RAG System
          </h1>
          <p className="font-mono text-[11px] uppercase tracking-[0.24em] text-dim">
            Holdings verified nightly
          </p>
        </div>
        <p className="mt-3 max-w-2xl leading-6 text-mist">
          A production-grade retrieval-augmented generation pipeline with
          hybrid retrieval, cross-encoder reranking, context compression, and
          RAGAS evaluation.
        </p>
        {health && (
          <p className="mt-3 font-mono text-[11px] uppercase tracking-[0.2em] text-mist">
            Environment <span className="text-gold">{health.environment}</span>
            {"  ·  "}LLM backend{" "}
            <span className="text-gold">{health.llm_backend}</span>
          </p>
        )}
      </div>

      <div className="bg-panel px-6 py-4">
        <div className="flex flex-col divide-y divide-line-soft border-y border-line">
          {[
            ["Documents shelved", health?.documents_count],
            ["Chunks indexed", health?.chunks_count],
            ["Audits on record", health?.eval_runs_count],
          ].map(([label, value]) => (
            <div key={label as string} className="flex items-baseline gap-3 py-2">
              <span className="text-sm font-semibold uppercase tracking-[0.14em] text-mist">
                {label}
              </span>
              <span
                aria-hidden="true"
                className="mx-1 flex-1 border-b border-dotted border-line"
              />
              <span className="font-display text-3xl font-bold tabular-nums text-gold">
                {value ?? (error ? "—" : "…")}
              </span>
            </div>
          ))}
        </div>
      </div>
      {error && (
        <p className="border-y border-bad bg-bad/10 p-4 text-sm text-ink">
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
            className="group flex flex-col bg-panel p-6 transition-colors hover:bg-hover"
          >
            <div className="font-mono text-[11px] font-semibold uppercase tracking-[0.24em] text-signal">
              {card.step}
            </div>
            <div className="mt-2 font-display text-3xl font-bold text-ink">
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

      <div className="bg-panel p-6">
        <p className="font-mono text-[11px] uppercase tracking-[0.24em] text-dim">
          Pipeline colophon
        </p>
        <pre className="mt-2 overflow-x-auto border border-line-soft bg-abyss p-4 font-mono text-xs leading-6 text-mist">
          {`DOCUMENTS > LOADER (PDF/MD/TXT) > CHUNKER > BGE EMBEDDINGS
  > CHROMADB (VECTOR) + BM25 INDEX (KEYWORD)

QUERY > VECTOR SEARCH + BM25 > RRF FUSION > RERANKER
  > COMPRESSION > PROMPT + CITATIONS > LLM > ANSWER`}
        </pre>
      </div>
    </div>
  );
}
