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

  const inputCls =
    "rounded-lg border border-line bg-abyss px-3 py-2 text-sm text-ink outline-none placeholder:text-dim focus:border-signal";
  const buttonCls =
    "rounded-lg bg-signal px-4 py-1.5 text-sm font-semibold text-signal-ink transition hover:brightness-110 disabled:opacity-40";

  return (
    <div className="flex flex-col gap-6">
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-signal">
          Load
        </p>
        <h1 className="mt-1 font-display text-3xl font-semibold tracking-tight text-ink">
          Document ingestion
        </h1>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <section className="flex flex-col gap-3 rounded-xl border border-line bg-raised p-5">
          <h2 className="font-display text-lg font-semibold text-ink">
            Upload file
          </h2>
          <input
            type="file"
            accept=".pdf,.md,.markdown,.txt"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="text-sm text-mist file:mr-3 file:rounded-md file:border file:border-line file:bg-abyss file:px-3 file:py-1.5 file:text-sm file:font-semibold file:text-ink hover:file:border-signal/60"
          />
          <input
            value={fileTitle}
            onChange={(e) => setFileTitle(e.target.value)}
            placeholder="Document title (defaults to filename)"
            className={inputCls}
          />
          <button
            onClick={() => file && run(() => api.ingestFile(file, fileTitle))}
            disabled={!file || loading}
            className={buttonCls}
          >
            Ingest document
          </button>
        </section>

        <section className="flex flex-col gap-3 rounded-xl border border-line bg-raised p-5">
          <h2 className="font-display text-lg font-semibold text-ink">
            Paste text
          </h2>
          <textarea
            value={rawText}
            onChange={(e) => setRawText(e.target.value)}
            rows={6}
            placeholder="Paste your document text here…"
            className={inputCls}
          />
          <input
            value={textTitle}
            onChange={(e) => setTextTitle(e.target.value)}
            placeholder="Document title"
            className={inputCls}
          />
          <button
            onClick={() =>
              rawText && run(() => api.ingestText(textTitle, rawText))
            }
            disabled={!rawText || loading}
            className={buttonCls}
          >
            Ingest text
          </button>
        </section>
      </div>

      {loading && <p className="text-sm text-mist">Processing…</p>}
      {error && (
        <p className="rounded-lg border border-bad/50 bg-bad/10 p-3 text-sm text-ink">
          {error}
        </p>
      )}
      {result && (
        <section className="rounded-xl border border-good/40 bg-raised p-5">
          <p className="text-sm text-ink">
            Ingested <strong>{result.title}</strong> —{" "}
            <strong className="font-mono text-gold">
              {result.chunk_count}
            </strong>{" "}
            chunks{" "}
            <span className="font-mono text-xs text-dim">
              ({result.doc_id})
            </span>
          </p>
          <div className="mt-3 flex flex-col gap-2">
            {result.sample_chunks.map((c) => (
              <div
                key={c.chunk_id}
                className="rounded bg-abyss px-3 py-2 text-sm"
              >
                <div className="font-mono text-xs text-dim">
                  {c.chunk_id} · {c.token_count} tokens
                  {c.section_header ? ` · ${c.section_header}` : ""}
                </div>
                <div className="mt-1 leading-5 text-mist">
                  {c.text_preview}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
