"use client";

import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type Health } from "@/lib/api";

const CARDS = [
  {
    href: "/ingest",
    step: "01 / LOAD",
    title: "Ingest",
    body: "Upload PDF/Markdown/text. Context-aware chunking preserves document structure.",
  },
  {
    href: "/ask",
    step: "02 / QUERY",
    title: "Ask",
    body: "Cited answers with the full retrieval debug: BM25, vector, fusion, rerank.",
  },
  {
    href: "/eval",
    step: "03 / PROVE",
    title: "Evaluate",
    body: "RAGAS scorecards and vector-only vs hybrid+rerank comparisons.",
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
    <div className="flex flex-col gap-6">
      <div className="border border-line bg-panel p-5">
        <p className="font-mono text-[11px] font-semibold uppercase tracking-[0.24em] text-signal">
          Overview
        </p>
        <h1 className="mt-1 font-display text-4xl font-extrabold uppercase tracking-tight text-ink">
          Hybrid RAG System
        </h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-mist">
          A production-grade retrieval-augmented generation pipeline with
          hybrid retrieval, cross-encoder reranking, context compression, and
          RAGAS evaluation.
        </p>
        {health && (
          <div className="mt-3 flex flex-wrap gap-2 font-mono text-[11px]">
            <Badge variant="secondary">ENV {health.environment}</Badge>
            <Badge variant="secondary">LLM {health.llm_backend}</Badge>
          </div>
        )}
      </div>

      <div className="grid grid-cols-3 gap-px border border-line bg-line">
        {[
          ["Documents", health?.documents_count],
          ["Chunks", health?.chunks_count],
          ["Eval runs", health?.eval_runs_count],
        ].map(([label, value]) => (
          <div key={label as string} className="bg-panel p-5">
            <div className="font-mono text-[11px] font-semibold uppercase tracking-[0.2em] text-dim">
              {label}
            </div>
            <div className="mt-1 font-display text-5xl font-extrabold tabular-nums text-gold">
              {value ?? (error ? "—" : "…")}
            </div>
          </div>
        ))}
      </div>
      {error && (
        <p className="border border-bad bg-bad/10 p-3 text-sm text-ink">
          <span className="font-mono text-[11px] font-semibold uppercase tracking-[0.2em] text-bad">
            Backend unreachable
          </span>
          <br />
          {error}. Start it with{" "}
          <code className="font-mono text-mist">
            uvicorn app.main:app --port 8000
          </code>
          .
        </p>
      )}

      <div className="grid grid-cols-3 gap-px border border-line bg-line">
        {CARDS.map((card) => (
          <Link
            key={card.href}
            href={card.href}
            className="group flex flex-col bg-panel p-5 transition-colors hover:bg-hover"
          >
            <div className="font-mono text-[11px] font-semibold uppercase tracking-[0.2em] text-signal">
              {card.step}
            </div>
            <div className="mt-1 font-display text-2xl font-extrabold uppercase text-ink">
              {card.title}
            </div>
            <p className="mt-1 flex-1 text-sm leading-5 text-mist">
              {card.body}
            </p>
            <div className="mt-3">
              <span className="inline-block border border-line bg-raised px-3 py-1 font-mono text-[11px] font-semibold uppercase tracking-[0.18em] text-signal transition-colors group-hover:border-signal group-hover:bg-signal group-hover:text-signal-ink">
                Open →
              </span>
            </div>
          </Link>
        ))}
      </div>

      <pre className="overflow-x-auto border border-line bg-panel p-4 font-mono text-xs leading-5 text-mist">
        {`DOCUMENTS > LOADER (PDF/MD/TXT) > CHUNKER > BGE EMBEDDINGS
  > CHROMADB (VECTOR) + BM25 INDEX (KEYWORD)

QUERY > VECTOR SEARCH + BM25 > RRF FUSION > RERANKER
  > COMPRESSION > PROMPT + CITATIONS > LLM > ANSWER`}
      </pre>
    </div>
  );
}
