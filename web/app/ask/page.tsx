"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useEffect, useState } from "react";
import { api, type QueryResponse } from "@/lib/api";

function Hits({
  title,
  hits,
}: {
  title: string;
  hits: { chunk_id: string; score: number; text_preview: string }[];
}) {
  return (
    <details className="anim-in border border-line bg-panel" open={false}>
      <summary className="cursor-pointer list-none border-b border-line-soft px-4 py-2 text-sm font-semibold text-ink marker:hidden [&::-webkit-details-marker]:hidden">
        <span className="font-mono text-[11px] uppercase tracking-[0.2em] text-dim">
          {title}
        </span>{" "}
        <span className="font-mono text-xs font-semibold text-gold">
          [{hits.length}]
        </span>
      </summary>
      <div className="flex flex-col gap-px bg-line-soft">
        {hits.length === 0 && (
          <p className="bg-panel px-4 py-2 text-sm text-mist">No hits.</p>
        )}
        {hits.slice(0, 10).map((h) => (
          <div key={h.chunk_id} className="bg-panel px-4 py-2 text-sm">
            <div className="font-mono text-[11px] text-dim">
              {h.chunk_id} · SCORE {h.score.toFixed(4)}
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

  // Staggered entrance for fresh results (skipped for reduced motion).
  useEffect(() => {
    if (!result) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    let cancelled = false;
    import("animejs").then(({ animate, stagger }) => {
      if (cancelled) return;
      animate(".anim-in", {
        opacity: [0, 1],
        translateY: [8, 0],
        delay: stagger(60),
        duration: 220,
        ease: "outExpo",
      });
    });
    return () => {
      cancelled = true;
    };
  }, [result]);

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
    <div className="flex flex-col gap-px border border-line bg-line">
      <div className="bg-panel p-5">
        <p className="font-mono text-[11px] font-semibold uppercase tracking-[0.24em] text-signal">
          02 / Query
        </p>
        <h1 className="mt-1 font-display text-3xl font-bold uppercase tracking-tight text-ink">
          Ask a question
        </h1>
      </div>

      <div className="flex flex-col gap-3 bg-panel p-5">
        <Input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && question && !loading && ask()}
          placeholder="WHAT WOULD YOU LIKE TO KNOW?"
          className="rounded-none border-line bg-abyss font-mono text-[13px] uppercase tracking-wide text-ink placeholder:text-dim focus-visible:ring-signal"
        />
        <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-sm text-mist">
          <label className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.18em]">
            Mode
            <select
              value={mode}
              onChange={(e) => setMode(e.target.value)}
              className="border border-line bg-abyss px-2 py-1 text-ink outline-none focus:border-signal"
            >
              <option value="hybrid">hybrid</option>
              <option value="vector_only">vector_only</option>
            </select>
          </label>
          <label className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.18em]">
            Top-K
            <input
              type="number"
              min={1}
              max={20}
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="w-16 border border-line bg-abyss px-2 py-1 text-ink outline-none focus:border-signal"
            />
          </label>
          <Button
            onClick={ask}
            disabled={!question || loading}
            className="rounded-none font-mono text-xs font-bold uppercase tracking-[0.18em]"
          >
            {loading ? "Searching…" : "Ask"}
          </Button>
        </div>
      </div>

      {error && (
        <p className="border-y border-bad bg-bad/10 p-4 text-sm text-ink">
          <span className="font-mono text-[11px] font-semibold uppercase tracking-[0.2em] text-bad">
            Error
          </span>
          <br />
          {error}
        </p>
      )}

      {result && (
        <>
          <section className="anim-in border-y-2 border-signal bg-panel p-5">
            <h2 className="font-mono text-[11px] font-semibold uppercase tracking-[0.24em] text-signal">
              Answer
            </h2>
            <p className="mt-2 whitespace-pre-wrap text-[15px] leading-7 text-ink">
              {result.answer}
            </p>
          </section>

          <section className="flex flex-col gap-px bg-line-soft">
            <h2 className="bg-panel px-5 pb-1 pt-4 font-display text-lg font-bold uppercase text-ink">
              Citations{" "}
              <span className="font-mono text-sm font-semibold text-gold">
                [{result.citations.length}]
              </span>
            </h2>
            {result.citations.map((c, i) => (
              <div key={c.chunk_id} className="anim-in bg-panel px-5 py-3 text-sm">
                <div className="flex flex-wrap items-center gap-2 font-semibold text-ink">
                  <Badge className="rounded-none bg-signal font-mono text-[11px] font-bold text-signal-ink">
                    [{i + 1}]
                  </Badge>
                  {c.doc_title}
                </div>
                <div className="mt-1 font-mono text-[11px] text-dim">
                  {c.chunk_id}
                </div>
                <div className="mt-1 leading-5 text-mist">“{c.snippet}”</div>
              </div>
            ))}
          </section>

          <section className="flex flex-col gap-2 bg-panel p-5">
            <h2 className="font-display text-lg font-bold uppercase text-ink">
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
