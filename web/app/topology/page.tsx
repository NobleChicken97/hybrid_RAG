"use client";

/**
 * Cross-reference index (Option 1): the REAL retrieval path for one
 * question — query → reranked chunks (with cross-encoder scores) → cited
 * chunks. All data comes from POST /query's retrieval_debug; nothing is
 * hardcoded. A corpus-wide embedding map (UMAP) is deferred to v2.
 */

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useState } from "react";
import { api, type QueryResponse } from "@/lib/api";

const STAGES = ["BM25", "VECTOR", "RRF", "RERANK", "CITE"];

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
    <div className="flex flex-col gap-px border border-line bg-line">
      <div className="bg-panel p-6">
        <h1 className="font-display text-4xl font-bold tracking-tight text-ink">
          Cross-reference index
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-mist">
          The true retrieval path behind your question — every entry is a
          chunk the pipeline actually returned, with its cross-encoder score.
        </p>
      </div>

      <div className="flex gap-px bg-line-soft">
        <Input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && question && !loading && trace()}
          placeholder="Ask something to trace its references…"
          className="flex-1 border-0 bg-panel px-4 py-2 text-sm text-ink outline-none placeholder:text-dim focus-visible:ring-1 focus-visible:ring-inset focus-visible:ring-signal"
        />
        <Button
          onClick={trace}
          disabled={!question || loading}
          className="font-mono text-xs font-bold uppercase tracking-[0.18em]"
        >
          {loading ? "Tracing…" : "Trace"}
        </Button>
      </div>

      {error && (
        <p className="border-y border-bad bg-bad/10 p-5 text-sm text-ink">
          Trace failed: {error}. Check the question and try again.
        </p>
      )}

      {result && (
        <div className="flex flex-col items-stretch gap-px bg-line-soft">
          <div
            aria-hidden="true"
            className="flex items-center gap-0 overflow-x-auto bg-panel"
          >
            {STAGES.map((s, i) => (
              <span key={s} className="flex items-center">
                <span className="border-r border-line bg-signal px-4 py-2 font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-signal-ink">
                  {s}
                </span>
                {i < STAGES.length - 1 && (
                  <span className="border-r border-line bg-panel px-2 py-2 font-mono text-[11px] text-dim">
                    →
                  </span>
                )}
              </span>
            ))}
            <span className="flex-1 border-b border-line-soft" />
          </div>

          <div className="border-y-2 border-signal bg-panel px-6 py-3 text-sm font-semibold text-ink">
            {question}
          </div>
          <div className="bg-panel px-6 pb-1 pt-3 font-mono text-[11px] uppercase tracking-[0.24em] text-dim">
            Ranked entries
          </div>
          {result.retrieval_debug.reranked_order.map((h, i) => {
            const isCited = cited.has(h.chunk_id);
            return (
              <div key={h.chunk_id} className="bg-panel px-6 py-2 text-sm">
                <div
                  className={`border px-4 py-3 ${
                    isCited ? "border-good bg-good/10" : "border-line"
                  }`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="font-mono text-[11px] uppercase tracking-[0.14em] text-dim">
                      Entry {String(i + 1).padStart(2, "0")} · Call no.{" "}
                      {h.chunk_id}
                    </span>
                    <span className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold tabular-nums text-gold">
                        {h.score.toFixed(2)}
                      </span>
                      {isCited && (
                        <Badge className="bg-good font-mono text-[10px] font-bold uppercase tracking-[0.14em] text-abyss">
                          Cited
                        </Badge>
                      )}
                    </span>
                  </div>
                  <div className="mt-1 leading-5 text-mist">
                    {h.text_preview}…
                  </div>
                </div>
              </div>
            );
          })}
          <p className="bg-panel px-6 py-3 font-mono text-[11px] leading-5 text-dim">
            {result.citations.length} CITATIONS · BM25{" "}
            {result.retrieval_debug.bm25_hits.length} · VECTOR{" "}
            {result.retrieval_debug.vector_hits.length} · FUSED{" "}
            {result.retrieval_debug.fused_order.length}
          </p>
        </div>
      )}
    </div>
  );
}
