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
    <details className="rounded-lg border border-line bg-raised">
      <summary className="cursor-pointer px-4 py-2 text-sm font-semibold text-ink">
        {title}{" "}
        <span className="font-mono text-xs font-medium text-gold">
          ({hits.length})
        </span>
      </summary>
      <div className="flex flex-col gap-2 border-t border-line-soft p-3">
        {hits.length === 0 && (
          <p className="text-sm text-mist">No hits.</p>
        )}
        {hits.slice(0, 10).map((h) => (
          <div
            key={h.chunk_id}
            className="rounded border-l-2 border-signal/60 bg-abyss px-3 py-2 text-sm"
          >
            <div className="font-mono text-xs text-dim">
              {h.chunk_id} · {h.score.toFixed(4)}
            </div>
            <div className="mt-1 leading-5 text-mist">{h.text_preview}…</div>
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
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-signal">
          Query
        </p>
        <h1 className="mt-1 font-display text-3xl font-semibold tracking-tight text-ink">
          Ask a question
        </h1>
      </div>

      <div className="flex flex-col gap-3 rounded-xl border border-line bg-raised p-4">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && question && !loading && ask()}
          placeholder="What would you like to know?"
          className="rounded-lg border border-line bg-abyss px-3 py-2 text-sm text-ink outline-none placeholder:text-dim focus:border-signal"
        />
        <div className="flex flex-wrap items-center gap-4 text-sm text-mist">
          <label className="flex items-center gap-2">
            Mode
            <select
              value={mode}
              onChange={(e) => setMode(e.target.value)}
              className="rounded-md border border-line bg-abyss px-2 py-1 text-ink outline-none focus:border-signal"
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
              className="w-16 rounded-md border border-line bg-abyss px-2 py-1 text-ink outline-none focus:border-signal"
            />
          </label>
          <button
            onClick={ask}
            disabled={!question || loading}
            className="rounded-lg bg-signal px-4 py-1.5 text-sm font-semibold text-signal-ink transition hover:brightness-110 disabled:opacity-40"
          >
            {loading ? "Searching…" : "Ask"}
          </button>
        </div>
      </div>

      {error && (
        <p className="rounded-lg border border-bad/50 bg-bad/10 p-3 text-sm text-ink">
          {error}
        </p>
      )}

      {result && (
        <>
          <section className="rounded-xl border border-signal/40 bg-raised p-5">
            <h2 className="text-[11px] font-semibold uppercase tracking-[0.18em] text-signal">
              Answer
            </h2>
            <p className="mt-2 whitespace-pre-wrap text-[15px] leading-7 text-ink">
              {result.answer}
            </p>
          </section>

          <section className="flex flex-col gap-2">
            <h2 className="font-display text-lg font-semibold text-ink">
              Citations{" "}
              <span className="font-mono text-sm font-medium text-gold">
                ({result.citations.length})
              </span>
            </h2>
            {result.citations.map((c, i) => (
              <div
                key={c.chunk_id}
                className="rounded-lg border border-line bg-raised px-4 py-3 text-sm"
              >
                <div className="font-semibold text-ink">
                  [{i + 1}] {c.doc_title}
                </div>
                <div className="mt-0.5 font-mono text-xs text-dim">
                  {c.chunk_id}
                </div>
                <div className="mt-1 leading-5 text-mist">“{c.snippet}”</div>
              </div>
            ))}
          </section>

          <section className="flex flex-col gap-2">
            <h2 className="font-display text-lg font-semibold text-ink">
              Retrieval debug
            </h2>
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
