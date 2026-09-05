"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useEffect, useState } from "react";
import {
  api,
  type DocumentInfo,
  type Health,
  type PublicConfig,
} from "@/lib/api";

export default function SystemPage() {
  const [health, setHealth] = useState<Health | null>(null);
  const [config, setConfig] = useState<PublicConfig | null>(null);
  const [docs, setDocs] = useState<DocumentInfo[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.health(), api.config(), api.documents()])
      .then(([h, c, d]) => {
        setHealth(h);
        setConfig(c);
        setDocs(d);
      })
      .catch((e: Error) => setError(e.message));
  }, []);

  if (error)
    return (
      <p className="border border-bad bg-bad/10 p-4 text-sm text-ink">
        <span className="font-mono text-[11px] font-semibold uppercase tracking-[0.2em] text-bad">
          Backend unreachable
        </span>
        <br />
        {error}
      </p>
    );
  if (!health || !config)
    return (
      <p className="font-mono text-xs uppercase tracking-[0.2em] text-mist">
        Loading system state…
      </p>
    );

  const rows: [string, string][] = [
    ["Environment", config.environment],
    ["LLM backend", `${config.llm_backend} (${config.generation_model})`],
    ["RAGAS judge", `${config.judge_backend} (${config.judge_model})`],
    ["Embedding model", config.embedding_model],
    ["Reranker model", config.reranker_model],
    [
      "Retrieval",
      `top_k=${config.retrieval_top_k} · rerank_top_n=${config.rerank_top_n} · rrf_k=${config.rrf_k}`,
    ],
    [
      "Compression",
      `threshold=${config.compression_threshold} · max_tokens=${config.max_context_tokens}`,
    ],
  ];

  return (
    <div className="flex flex-col gap-px border border-line bg-line">
      <div className="bg-panel p-5">
        <p className="font-mono text-[11px] font-semibold uppercase tracking-[0.24em] text-signal">
          Inspect
        </p>
        <h1 className="mt-1 font-display text-3xl font-extrabold uppercase tracking-tight text-ink">
          System
        </h1>
      </div>

      <div className="grid grid-cols-3 gap-px bg-line">
        {[
          ["Documents", health.documents_count],
          ["Chunks", health.chunks_count],
          ["Eval runs", health.eval_runs_count],
        ].map(([label, value]) => (
          <div key={label as string} className="bg-panel p-5">
            <div className="font-mono text-[11px] font-semibold uppercase tracking-[0.2em] text-dim">
              {label}
            </div>
            <div className="mt-1 font-display text-5xl font-extrabold tabular-nums text-gold">
              {value}
            </div>
          </div>
        ))}
      </div>

      <section className="bg-panel p-5">
        <h2 className="font-display text-lg font-extrabold uppercase text-ink">
          Configuration
        </h2>
        <dl className="mt-2 divide-y divide-line-soft border-y border-line-soft text-sm">
          {rows.map(([k, v]) => (
            <div key={k} className="flex justify-between gap-4 py-2">
              <dt className="font-mono text-[11px] uppercase tracking-[0.16em] text-mist">
                {k}
              </dt>
              <dd className="text-right font-mono text-xs text-ink">{v}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section className="bg-panel">
        <h2 className="px-5 pb-1 pt-4 font-display text-lg font-extrabold uppercase text-ink">
          Documents{" "}
          <span className="font-mono text-sm font-semibold text-gold">
            [{docs.length}]
          </span>
        </h2>
        <div className="overflow-x-auto p-5 pt-2">
          <Table className="border border-line-soft font-mono text-xs">
            <TableHeader className="bg-raised">
              <TableRow className="border-b border-line hover:bg-transparent">
                <TableHead className="text-dim">TITLE</TableHead>
                <TableHead className="text-dim">DOC ID</TableHead>
                <TableHead className="text-dim">CHUNKS</TableHead>
                <TableHead className="text-dim">INGESTED</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {docs.map((d) => (
                <TableRow
                  key={d.doc_id}
                  className="border-b border-line-soft text-mist last:border-0 hover:bg-hover"
                >
                  <TableCell className="font-sans text-sm font-semibold text-ink">
                    {d.title}
                  </TableCell>
                  <TableCell className="text-dim">{d.doc_id}</TableCell>
                  <TableCell className="tabular-nums text-gold">
                    {d.chunk_count}
                  </TableCell>
                  <TableCell className="text-dim">
                    {d.ingested_at ?? "—"}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </section>
    </div>
  );
}
