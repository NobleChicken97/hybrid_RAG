"use client";

import { useState } from "react";
import { api, type IngestResponse } from "@/lib/api";

export default function IngestPage() {
  const [file, setFile] = useState<File | null>(null);
  const [fileTitle, setFileTitle] = useState("");
  const [rawText, setRawText] = useState("");
  const [textTitle, setTextTitle] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<IngestResponse | null>(null);

  async function run(fn: () => Promise<IngestResponse>) {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(await fn());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold tracking-tight">
        📄 Document ingestion
      </h1>

      <div className="grid grid-cols-2 gap-4">
        <section className="flex flex-col gap-3 rounded-xl border border-zinc-200 bg-white p-4">
          <h2 className="font-medium">📁 Upload file</h2>
          <input
            type="file"
            accept=".pdf,.md,.markdown,.txt"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="text-sm"
          />
          <input
            value={fileTitle}
            onChange={(e) => setFileTitle(e.target.value)}
            placeholder="Document title (defaults to filename)"
            className="rounded-lg border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
          />
          <button
            onClick={() => file && run(() => api.ingestFile(file, fileTitle))}
            disabled={!file || loading}
            className="rounded-lg bg-zinc-900 px-4 py-1.5 text-sm font-medium text-white disabled:opacity-40"
          >
            🚀 Ingest document
          </button>
        </section>

        <section className="flex flex-col gap-3 rounded-xl border border-zinc-200 bg-white p-4">
          <h2 className="font-medium">📝 Paste text</h2>
          <textarea
            value={rawText}
            onChange={(e) => setRawText(e.target.value)}
            rows={6}
            placeholder="Paste your document text here…"
            className="rounded-lg border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
          />
          <input
            value={textTitle}
            onChange={(e) => setTextTitle(e.target.value)}
            placeholder="Document title"
            className="rounded-lg border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
          />
          <button
            onClick={() =>
              rawText && run(() => api.ingestText(textTitle, rawText))
            }
            disabled={!rawText || loading}
            className="rounded-lg bg-zinc-900 px-4 py-1.5 text-sm font-medium text-white disabled:opacity-40"
          >
            🚀 Ingest text
          </button>
        </section>
      </div>

      {loading && <p className="text-sm text-zinc-500">Processing…</p>}
      {error && (
        <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </p>
      )}
      {result && (
        <section className="rounded-xl border border-zinc-200 bg-white p-4">
          <p className="text-sm">
            ✅ Ingested <strong>{result.title}</strong> —{" "}
            <strong>{result.chunk_count}</strong> chunks ({result.doc_id})
          </p>
          <div className="mt-3 flex flex-col gap-2">
            {result.sample_chunks.map((c) => (
              <div
                key={c.chunk_id}
                className="rounded bg-zinc-50 px-3 py-2 text-sm"
              >
                <div className="font-mono text-xs text-zinc-500">
                  📦 {c.chunk_id} · {c.token_count} tokens
                  {c.section_header ? ` · 📑 ${c.section_header}` : ""}
                </div>
                <div className="mt-1 text-zinc-700">{c.text_preview}</div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
