"use client";

/**
 * Knowledge topology (Option 1): visualize the REAL retrieval path for one
 * question — query → reranked chunks (with cross-encoder scores) → cited
 * chunks. All data comes from POST /query's retrieval_debug; nothing is
 * hardcoded. A corpus-wide embedding map (UMAP) is deferred to v2.
 */

import { useState } from "react";
import { api, type QueryResponse } from "@/lib/api";

export default function TopologyPage() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<QueryResponse | null>(null);

  async function trace() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(await api.query(question, "hybrid", 5));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  const cited = new Set((result?.citations ?? []).map((c) => c.chunk_id));

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">
          🕸️ Knowledge topology
        </h1>
        <p className="mt-1 text-sm text-zinc-600">
          The real retrieval path for your question — every node is a chunk
          the pipeline actually returned, with its cross-encoder score.
        </p>
      </div>

      <div className="flex gap-2">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && question && !loading && trace()}
          placeholder="Ask something to trace its retrieval path…"
          className="flex-1 rounded-lg border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
        />
        <button
          onClick={trace}
          disabled={!question || loading}
          className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
        >
          {loading ? "Tracing…" : "Trace"}
        </button>
      </div>

      {error && (
        <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </p>
      )}

      {result && (
        <div className="flex flex-col items-stretch gap-2">
          <div className="rounded-xl bg-zinc-900 px-4 py-3 text-sm font-medium text-white">
            ❓ {question}
          </div>
          <div className="self-center text-zinc-400">▼ reranked ▼</div>
          {result.retrieval_debug.reranked_order.map((h, i) => (
            <div key={h.chunk_id}>
              <div
                className={`rounded-xl border px-4 py-2 text-sm ${
                  cited.has(h.chunk_id)
                    ? "border-green-600 bg-green-50"
                    : "border-zinc-200 bg-white"
                }`}
              >
                <div className="flex justify-between gap-2">
                  <span className="font-mono text-xs text-zinc-500">
                    #{i + 1} {h.chunk_id}
                  </span>
                  <span className="font-mono text-xs">
                    {h.score.toFixed(2)}
                    {cited.has(h.chunk_id) && " · cited ✓"}
                  </span>
                </div>
                <div className="mt-1 text-zinc-700">{h.text_preview}…</div>
              </div>
              {i < result.retrieval_debug.reranked_order.length - 1 && (
                <div className="py-1 text-center text-zinc-300">│</div>
              )}
            </div>
          ))}
          <p className="mt-2 text-xs text-zinc-500">
            Green = chunk cited in the answer (
            {result.citations.length} citations). BM25 hits:{" "}
            {result.retrieval_debug.bm25_hits.length} · Vector hits:{" "}
            {result.retrieval_debug.vector_hits.length} · Fused:{" "}
            {result.retrieval_debug.fused_order.length}
          </p>
        </div>
      )}
    </div>
  );
}
