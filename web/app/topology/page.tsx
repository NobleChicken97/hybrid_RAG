"use client";

/**
 * Knowledge topology (Option 1): visualize the REAL retrieval path for one
 * question — query → reranked chunks (with cross-encoder scores) → cited
 * chunks. All data comes from POST /query's retrieval_debug; nothing is
 * hardcoded. A corpus-wide embedding map (UMAP) is deferred to v2.
 */

import { useState } from "react";
import { api, type QueryResponse } from "@/lib/api";

const STAGES = ["BM25", "Vector", "RRF", "Rerank", "Cite"];

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
        <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-signal">
          Trace
        </p>
        <h1 className="mt-1 font-display text-3xl font-semibold tracking-tight text-ink">
          Knowledge topology
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-5 text-mist">
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
          className="flex-1 rounded-lg border border-line bg-raised px-3 py-2 text-sm text-ink outline-none placeholder:text-dim focus:border-signal"
        />
        <button
          onClick={trace}
          disabled={!question || loading}
          className="rounded-lg bg-signal px-4 py-2 text-sm font-semibold text-signal-ink transition hover:brightness-110 disabled:opacity-40"
        >
          {loading ? "Tracing…" : "Trace"}
        </button>
      </div>

      {error && (
        <p className="rounded-lg border border-bad/50 bg-bad/10 p-3 text-sm text-ink">
          {error}
        </p>
      )}

      {result && (
        <div className="flex flex-col items-stretch gap-2">
          {/* Pipeline stage strip: the circuit motif for this page. */}
          <div
            aria-hidden="true"
            className="mb-1 flex items-center gap-1.5 overflow-x-auto rounded-xl border border-line-soft bg-panel px-4 py-3"
          >
            {STAGES.map((s, i) => (
              <span key={s} className="flex items-center gap-1.5">
                <span className="rounded-md border border-signal/40 bg-signal/10 px-2.5 py-1 font-mono text-[11px] font-semibold uppercase tracking-[0.12em] text-signal">
                  {s}
                </span>
                {i < STAGES.length - 1 && (
                  <span className="text-dim">→</span>
                )}
              </span>
            ))}
          </div>

          <div className="rounded-xl border border-signal/40 bg-raised px-4 py-3 text-sm font-medium text-ink">
            {question}
          </div>
          <div className="self-center font-mono text-[11px] uppercase tracking-[0.2em] text-dim">
            reranked
          </div>
          {result.retrieval_debug.reranked_order.map((h, i) => {
            const isCited = cited.has(h.chunk_id);
            return (
              <div key={h.chunk_id}>
                <div
                  className={`rounded-xl border px-4 py-3 text-sm ${
                    isCited
                      ? "border-good/60 bg-good/10"
                      : "border-line bg-raised"
                  }`}
                >
                  <div className="flex justify-between gap-2">
                    <span className="font-mono text-xs text-dim">
                      #{i + 1} {h.chunk_id}
                    </span>
                    <span className="font-mono text-xs font-semibold text-gold">
                      {h.score.toFixed(2)}
                      {isCited && (
                        <span className="ml-2 rounded bg-good/20 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-good">
                          cited
                        </span>
                      )}
                    </span>
                  </div>
                  <div className="mt-1 leading-5 text-mist">
                    {h.text_preview}…
                  </div>
                </div>
                {i < result.retrieval_debug.reranked_order.length - 1 && (
                  <div className="py-1 text-center text-line">│</div>
                )}
              </div>
            );
          })}
          <p className="mt-2 font-mono text-xs leading-5 text-dim">
            {result.citations.length} citations · BM25 hits:{" "}
            {result.retrieval_debug.bm25_hits.length} · Vector hits:{" "}
            {result.retrieval_debug.vector_hits.length} · Fused:{" "}
            {result.retrieval_debug.fused_order.length}
          </p>
        </div>
      )}
    </div>
  );
}
