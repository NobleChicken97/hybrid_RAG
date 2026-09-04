"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type Health } from "@/lib/api";

const CARDS = [
  {
    href: "/ingest",
    title: "📄 Ingest",
    body: "Upload PDF/Markdown/text. Context-aware chunking preserves document structure.",
  },
  {
    href: "/ask",
    title: "💬 Ask",
    body: "Cited answers with the full retrieval debug: BM25, vector, fusion, rerank.",
  },
  {
    href: "/eval",
    title: "📊 Evaluate",
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
        <h1 className="text-3xl font-semibold tracking-tight">
          Hybrid RAG System
        </h1>
        <p className="mt-2 max-w-2xl text-zinc-600">
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
            className="rounded-xl border border-zinc-200 bg-white p-4"
          >
            <div className="text-xs uppercase tracking-wide text-zinc-500">
              {label}
            </div>
            <div className="mt-1 text-2xl font-semibold">
              {value ?? (error ? "—" : "…")}
            </div>
          </div>
        ))}
      </div>
      {error && (
        <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          Cannot reach backend: {error}. Start it with{" "}
          <code className="font-mono">uvicorn app.main:app --port 8000</code>.
        </p>
      )}
      {health && (
        <p className="text-sm text-zinc-500">
          Environment <code className="font-mono">{health.environment}</code> ·{" "}
          LLM backend <code className="font-mono">{health.llm_backend}</code>
        </p>
      )}

      <div className="grid grid-cols-3 gap-4">
        {CARDS.map((card) => (
          <Link
            key={card.href}
            href={card.href}
            className="rounded-xl border border-zinc-200 bg-white p-5 hover:border-zinc-400"
          >
            <div className="font-medium">{card.title}</div>
            <p className="mt-1 text-sm text-zinc-600">{card.body}</p>
            <div className="mt-3 text-sm font-medium text-zinc-900">
              Open →
            </div>
          </Link>
        ))}
      </div>

      <pre className="overflow-x-auto rounded-xl bg-zinc-950 p-4 text-xs leading-5 text-zinc-100">
        {`Documents → Loader (PDF/MD/TXT) → Chunker → BGE Embeddings
→ ChromaDB (vector) + BM25 Index (keyword)

Query → Vector Search + BM25 → RRF Fusion → Reranker
→ Compression → Prompt + Citations → LLM → Answer`}
      </pre>
    </div>
  );
}
