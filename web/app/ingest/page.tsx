"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
    "border-line bg-abyss text-ink placeholder:text-dim focus-visible:ring-signal";

  return (
    <div className="flex flex-col gap-px border border-line bg-line">
      <div className="bg-panel p-6">
        <h1 className="font-display text-4xl font-bold tracking-tight text-ink">
          Shelve a document
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-mist">
          Hand over a file or paste text. The room catalogs it into indexed
          chunks, each with its own call number.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-px bg-line-soft">
        <section className="flex flex-col gap-3 bg-panel p-6">
          <h2 className="font-display text-xl font-bold text-ink">
            Deposit a file
          </h2>
          <input
            type="file"
            accept=".pdf,.md,.markdown,.txt"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="text-sm text-mist file:mr-3 file:border file:border-line file:bg-abyss file:px-3 file:py-1.5 file:font-mono file:text-[11px] file:font-bold file:uppercase file:tracking-[0.14em] file:text-ink hover:file:border-signal"
          />
          <Input
            value={fileTitle}
            onChange={(e) => setFileTitle(e.target.value)}
            placeholder="Document title (defaults to filename)"
            className={inputCls}
          />
          <Button
            onClick={() => file && run(() => api.ingestFile(file, fileTitle))}
            disabled={!file || loading}
            className="font-mono text-xs font-bold uppercase tracking-[0.18em]"
          >
            Shelve document
          </Button>
        </section>

        <section className="flex flex-col gap-3 bg-panel p-6">
          <h2 className="font-display text-xl font-bold text-ink">
            Transcribe text
          </h2>
          <textarea
            value={rawText}
            onChange={(e) => setRawText(e.target.value)}
            rows={6}
            placeholder="Paste your document text here…"
            className="border border-line bg-abyss px-3 py-2 text-sm text-ink outline-none placeholder:text-dim focus:border-signal"
          />
          <Input
            value={textTitle}
            onChange={(e) => setTextTitle(e.target.value)}
            placeholder="Document title"
            className={inputCls}
          />
          <Button
            onClick={() =>
              rawText && run(() => api.ingestText(textTitle, rawText))
            }
            disabled={!rawText || loading}
            className="font-mono text-xs font-bold uppercase tracking-[0.18em]"
          >
            Shelve text
          </Button>
        </section>
      </div>

      {loading && (
        <p className="bg-panel p-4 font-mono text-xs uppercase tracking-[0.2em] text-mist">
          Cataloging…
        </p>
      )}
      {error && (
        <p className="border-y border-bad bg-bad/10 p-5 text-sm text-ink">
          Deposit failed: {error}. Check the file and try again.
        </p>
      )}
      {result && (
        <section className="border-t-2 border-good bg-panel p-6">
          <p className="font-display text-xl font-bold text-ink">
            Shelved under {result.chunk_count} call numbers
          </p>
          <p className="mt-1 font-mono text-[11px] uppercase tracking-[0.16em] text-mist">
            {result.title} · {result.doc_id}
          </p>
          <div className="mt-3 flex flex-col divide-y divide-line-soft border-y border-line-soft">
            {result.sample_chunks.map((c) => (
              <div key={c.chunk_id} className="py-2 text-sm">
                <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-gold">
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
