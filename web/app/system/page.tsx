"use client";

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
      <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
        Cannot reach backend: {error}
      </p>
    );
  if (!health || !config)
    return <p className="text-sm text-zinc-500">Loading system state…</p>;

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
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold tracking-tight">⚙️ System</h1>

      <div className="grid grid-cols-3 gap-4">
        {[
          ["Documents", health.documents_count],
          ["Chunks", health.chunks_count],
          ["Eval runs", health.eval_runs_count],
        ].map(([label, value]) => (
          <div
            key={label as string}
            className="rounded-xl border border-zinc-200 bg-white p-4"
          >
            <div className="text-xs uppercase tracking-wide text-zinc-500">
              {label}
            </div>
            <div className="mt-1 text-2xl font-semibold">{value}</div>
          </div>
        ))}
      </div>

      <section className="rounded-xl border border-zinc-200 bg-white p-4">
        <h2 className="font-medium">Configuration</h2>
        <dl className="mt-2 divide-y divide-zinc-100 text-sm">
          {rows.map(([k, v]) => (
            <div key={k} className="flex justify-between gap-4 py-1.5">
              <dt className="text-zinc-500">{k}</dt>
              <dd className="font-mono text-xs">{v}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section className="rounded-xl border border-zinc-200 bg-white p-4">
        <h2 className="font-medium">📚 Documents ({docs.length})</h2>
        <div className="mt-2 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-zinc-200 text-xs uppercase text-zinc-500">
                <th className="px-3 py-2">Title</th>
                <th className="px-3 py-2">Doc ID</th>
                <th className="px-3 py-2">Chunks</th>
                <th className="px-3 py-2">Ingested</th>
              </tr>
            </thead>
            <tbody>
              {docs.map((d) => (
                <tr key={d.doc_id} className="border-b border-zinc-100">
                  <td className="px-3 py-2">{d.title}</td>
                  <td className="px-3 py-2 font-mono text-xs">{d.doc_id}</td>
                  <td className="px-3 py-2">{d.chunk_count}</td>
                  <td className="px-3 py-2 text-xs text-zinc-500">
                    {d.ingested_at ?? "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
