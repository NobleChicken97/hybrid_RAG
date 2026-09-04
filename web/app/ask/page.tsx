"use client";

import { useState } from "react";
import { api, type QueryResponse } from "@/lib/api";

function Hits({
  title,
  hits,
}: {
  title: string;
  hits: { chunk_id: string; score: number; text_preview: string }[];
}) {
  return (
    <details className="rounded-lg border border-zinc-200 bg-white">
      <summary className="cursor-pointer px-4 py-2 text-sm font-medium">
        {title} ({hits.length})
      </summary>
      <div className="flex flex-col gap-2 border-t border-zinc-100 p-3">
        {hits.length === 0 && (
          <p className="text-sm text-zinc-500">No hits.</p>
        )}
        {hits.slice(0, 10).map((h) => (
          <div
            key={h.chunk_id}
            className="rounded border-l-2 border-zinc-300 bg-zinc-50 px-3 py-2 text-sm"
          >
            <div className="font-mono text-xs text-zinc-500">
              {h.chunk_id} · {h.score.toFixed(4)}
            </div>
            <div className="mt-1 text-zinc-700">{h.text_preview}…</div>
          </div>
        ))}
      </div>
    </details>
  );
}

export default function AskPage() {
  const [question, setQuestion] = useState("");
  const [mode, setMode] = useState("hybrid");
  const [topK, setTopK] = useState(5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<QueryResponse | null>(null);

  async function ask() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(await api.query(question, mode, topK));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold tracking-tight">
        💬 Ask a question
      </h1>

      <div className="flex flex-col gap-3 rounded-xl border border-zinc-200 bg-white p-4">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && question && !loading && ask()}
          placeholder="What would you like to know?"
          className="rounded-lg border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
        />
        <div className="flex items-center gap-4 text-sm">
          <label className="flex items-center gap-2">
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
          <label className="flex items-center gap-2">
            Top-K
            <input
              type="number"
              min={1}
              max={20}
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="w-16 rounded border border-zinc-300 px-2 py-1"
            />
          </label>
          <button
            onClick={ask}
            disabled={!question || loading}
            className="rounded-lg bg-zinc-900 px-4 py-1.5 text-sm font-medium text-white disabled:opacity-40"
          >
            {loading ? "Searching…" : "🔍 Ask"}
          </button>
        </div>
      </div>

      {error && (
        <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </p>
      )}

      {result && (
        <>
          <section className="rounded-xl border border-zinc-200 bg-white p-4">
            <h2 className="font-medium">📝 Answer</h2>
            <p className="mt-2 whitespace-pre-wrap text-sm leading-6">
              {result.answer}
            </p>
          </section>

          <section className="flex flex-col gap-2">
            <h2 className="font-medium">
              📌 Citations ({result.citations.length})
            </h2>
            {result.citations.map((c, i) => (
              <div
                key={c.chunk_id}
                className="rounded-lg border border-zinc-200 bg-white px-4 py-2 text-sm"
              >
                <div className="font-medium">
                  [{i + 1}] {c.doc_title}
                </div>
                <div className="font-mono text-xs text-zinc-500">
                  {c.chunk_id}
                </div>
                <div className="mt-1 text-zinc-600">“{c.snippet}”</div>
              </div>
            ))}
          </section>

          <section className="flex flex-col gap-2">
            <h2 className="font-medium">🔧 Retrieval debug</h2>
            <Hits title="BM25 hits" hits={result.retrieval_debug.bm25_hits} />
            <Hits
              title="Vector hits"
              hits={result.retrieval_debug.vector_hits}
            />
            <Hits
              title="Fused order"
              hits={result.retrieval_debug.fused_order}
            />
            <Hits
              title="Reranked"
              hits={result.retrieval_debug.reranked_order}
            />
          </section>
        </>
      )}
    </div>
  );
}
