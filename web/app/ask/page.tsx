"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Reveal } from "@/components/reveal";
import { useEffect, useState } from "react";
import { api, type Health, type QueryResponse } from "@/lib/api";

function Hits({
  title,
  hits,
}: {
  title: string;
  hits: { chunk_id: string; score: number; text_preview: string }[];
}) {
  return (
    <details className="border border-line bg-panel">
      <summary className="cursor-pointer list-none border-b border-line-soft px-4 py-2 marker:hidden [&::-webkit-details-marker]:hidden">
        <span className="text-sm font-bold uppercase tracking-[0.14em] text-ink">
          {title}
        </span>{" "}
        <span className="font-mono text-xs font-semibold text-gold">
          [{hits.length}]
        </span>
      </summary>
      <div className="flex flex-col divide-y divide-line-soft">
        {hits.length === 0 && (
          <p className="px-4 py-2 text-sm text-mist">No hits.</p>
        )}
        {hits.slice(0, 10).map((h) => (
          <div key={h.chunk_id} className="px-4 py-2 text-sm">
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
  const [health, setHealth] = useState<Health | null>(null);

  useEffect(() => {
    api
      .health()
      .then(setHealth)
      .catch(() => {});
  }, []);

  // The single authored motion moment in this world: fresh evidence
  // arrives as a slip rising into lamplight (rise + deblur, one batch,
  // exponential out). Skipped for reduced motion.
  useEffect(() => {
    if (!result) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    let cancelled = false;
    import("animejs").then(({ animate, stagger }) => {
      if (cancelled) return;
      animate(".evidence-in", {
        opacity: [0, 1],
        translateY: [14, 0],
        filter: ["blur(6px)", "blur(0px)"],
        delay: stagger(90),
        duration: 420,
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
      <div className="bg-abyss p-6 sm:p-10">
        <div className="grid items-center gap-8 xl:grid-cols-12">
          <div className="xl:col-span-7">
            <h1 className="font-display text-5xl font-bold uppercase leading-[0.95] tracking-tight text-ink sm:text-7xl">
              Ask a<br />
              question.
            </h1>
            <p className="mt-3 max-w-xl text-sm leading-6 text-mist">
              Pose it plainly. The room answers on a slip, with every claim
              stamped to its shelf mark.
            </p>
          </div>
          <Reveal className="flex flex-col gap-px border border-line bg-line xl:col-span-5">
            <div className="bg-panel px-5 py-3 font-mono text-[11px] font-bold uppercase tracking-[0.24em] text-signal">
              Today in the stacks
            </div>
            <div className="flex flex-col bg-panel px-5 py-4">
              <div className="flex items-baseline justify-between border-b border-line-soft pb-2">
                <span className="text-sm font-semibold uppercase tracking-[0.14em] text-mist">
                  Documents
                </span>
                <span className="font-display text-2xl font-bold tabular-nums text-ink">
                  {health?.documents_count ?? "…"}
                </span>
              </div>
              <div className="flex items-baseline justify-between border-b border-line-soft py-2">
                <span className="text-sm font-semibold uppercase tracking-[0.14em] text-mist">
                  Chunks
                </span>
                <span className="font-display text-2xl font-bold tabular-nums text-ink">
                  {health?.chunks_count ?? "…"}
                </span>
              </div>
              <div className="flex items-baseline justify-between py-2">
                <span className="text-sm font-semibold uppercase tracking-[0.14em] text-mist">
                  Answer engine
                </span>
                <span className="font-mono text-xs text-ink">
                  {health ? `${health.llm_backend} · top 5` : "…"}
                </span>
              </div>
            </div>
          </Reveal>
        </div>
      </div>

      <div className="flex flex-col gap-3 bg-panel p-6">
        <Input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && question && !loading && ask()}
          placeholder="What would you like to know?"
          className="border-line bg-raised text-[15px] text-ink placeholder:text-dim focus-visible:ring-signal"
        />
        <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-sm text-mist">
          <label className="flex items-center gap-2 text-[13px] font-bold uppercase tracking-[0.14em]">
            Mode
            <select
              value={mode}
              onChange={(e) => setMode(e.target.value)}
              className="border border-line bg-raised px-2 py-1 text-ink outline-none focus:border-signal"
            >
              <option value="hybrid">hybrid</option>
              <option value="vector_only">vector_only</option>
            </select>
          </label>
          <label className="flex items-center gap-2 text-[13px] font-bold uppercase tracking-[0.14em]">
            Top-K
            <input
              type="number"
              min={1}
              max={20}
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="w-16 border border-line bg-raised px-2 py-1 text-ink outline-none focus:border-signal"
            />
          </label>
          <Button
            onClick={ask}
            disabled={!question || loading}
            className="font-mono text-xs font-bold uppercase tracking-[0.18em]"
          >
            {loading ? "Consulting the stacks…" : "Ask"}
          </Button>
        </div>
      </div>

      {error && (
        <p className="border-y border-bad bg-bad/10 p-5 text-sm text-ink">
          The request failed: {error}. Check the question and try again.
        </p>
      )}

      {result && (
        <div className="grid items-start gap-px bg-line-soft xl:grid-cols-12">
          <div className="flex flex-col gap-px bg-line-soft xl:col-span-7">
            <section className="evidence-in border-y-4 border-signal bg-paper p-6 text-paper-ink sm:p-8">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b-2 border-paper-ink/70 pb-2">
              <span className="font-display text-2xl font-bold uppercase">
                Evidence slip
              </span>
              <span className="bg-signal px-2 py-0.5 font-mono text-[10px] font-bold uppercase tracking-[0.2em] text-signal-ink">
                {result.citations.length} shelf mark
                {result.citations.length === 1 ? "" : "s"}
              </span>
            </div>
            <p className="mt-3 whitespace-pre-wrap font-display text-xl font-medium leading-8">
              {result.answer}
            </p>
          </section>

          <section className="flex flex-col gap-px bg-line-soft">
            <h2 className="bg-panel px-6 pb-1 pt-4 font-display text-2xl font-bold uppercase text-ink">
              Pulled cards{" "}
              <span className="font-mono text-sm font-semibold text-gold">
                [{result.citations.length}]
              </span>
            </h2>
            {result.citations.map((c, i) => (
              <div key={c.chunk_id} className="evidence-in bg-panel px-6 py-4 text-sm">
                <div className="border border-line bg-raised p-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge className="bg-signal font-mono text-[11px] font-bold text-signal-ink">
                      [{i + 1}]
                    </Badge>
                    <span className="font-bold text-ink">{c.doc_title}</span>
                  </div>
                  <div className="mt-1 font-mono text-[11px] uppercase tracking-[0.14em] text-gold">
                    Call no. {c.chunk_id}
                  </div>
                  <div className="mt-2 leading-6 text-mist">
                    “{c.snippet}”
                  </div>
                </div>
              </div>
            ))}
          </section>
          </div>

          <section className="flex flex-col gap-2 bg-panel p-6 xl:sticky xl:top-4">
            <h2 className="font-display text-2xl font-bold uppercase text-ink">
              Retrieval ledger
            </h2>
            <Hits title="BM25 entries" hits={result.retrieval_debug.bm25_hits} />
            <Hits
              title="Vector entries"
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
        </div>
      )}
    </div>
  );
}
