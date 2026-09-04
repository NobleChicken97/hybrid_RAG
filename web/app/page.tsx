"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type Health } from "@/lib/api";

const CARDS = [
  {
    href: "/ingest",
    eyebrow: "Step 01 — Load",
    title: "Ingest",
    body: "Upload PDF/Markdown/text. Context-aware chunking preserves document structure.",
  },
  {
    href: "/ask",
    eyebrow: "Step 02 — Query",
    title: "Ask",
    body: "Cited answers with the full retrieval debug: BM25, vector, fusion, rerank.",
  },
  {
    href: "/eval",
    eyebrow: "Step 03 — Prove",
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
    <div className="flex flex-col gap-8">
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-signal">
          Overview
        </p>
        <h1 className="mt-1 font-display text-4xl font-semibold tracking-tight text-ink">
          Hybrid RAG System
        </h1>
        <p className="mt-3 max-w-2xl leading-6 text-mist">
          A production-grade retrieval-augmented generation pipeline with
          hybrid retrieval, cross-encoder reranking, context compression, and
          RAGAS evaluation.
        </p>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {[
          ["Documents", health?.documents_count],
          ["Chunks", health?.chunks_count],
          ["Eval runs", health?.eval_runs_count],
        ].map(([label, value]) => (
          <div
            key={label as string}
            className="rounded-xl border border-line bg-raised p-5"
          >
            <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-dim">
              {label}
            </div>
            <div className="mt-1 font-display text-4xl font-semibold text-gold">
              {value ?? (error ? "—" : "…")}
            </div>
          </div>
        ))}
      </div>
      {error && (
        <p className="rounded-lg border border-bad/50 bg-bad/10 p-3 text-sm text-ink">
          Cannot reach backend: {error}. Start it with{" "}
          <code className="font-mono text-mist">
            uvicorn app.main:app --port 8000
          </code>
          .
        </p>
      )}
      {health && (
        <p className="text-sm text-mist">
          Environment <code className="font-mono">{health.environment}</code> ·{" "}
          LLM backend <code className="font-mono">{health.llm_backend}</code>
        </p>
      )}

      <div className="grid grid-cols-3 gap-4">
        {CARDS.map((card) => (
          <Link
            key={card.href}
            href={card.href}
            className="group rounded-xl border border-line bg-raised p-5 transition-colors hover:border-signal/60"
          >
            <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-signal">
              {card.eyebrow}
            </div>
            <div className="mt-1 font-display text-xl font-semibold text-ink">
              {card.title}
            </div>
            <p className="mt-1 text-sm leading-5 text-mist">{card.body}</p>
            <div className="mt-3 text-sm font-semibold text-signal">
              Open{" "}
              <span
                aria-hidden="true"
                className="inline-block transition-transform group-hover:translate-x-1"
              >
                →
              </span>
            </div>
          </Link>
        ))}
      </div>

      <pre className="overflow-x-auto rounded-xl border border-line-soft bg-panel p-4 font-mono text-xs leading-5 text-mist">
        {`Documents → Loader (PDF/MD/TXT) → Chunker → BGE Embeddings
→ ChromaDB (vector) + BM25 Index (keyword)

Query → Vector Search + BM25 → RRF Fusion → Reranker
→ Compression → Prompt + Citations → LLM → Answer`}
      </pre>
    </div>
  );
}
