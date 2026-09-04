/**
 * Typed client for the Hybrid RAG FastAPI backend.
 *
 * Two modes (2026-09-04 cutover):
 * - Local dev: set NEXT_PUBLIC_BACKEND_URL=http://localhost:8000 and the
 *   client talks to the backend directly (or via the Next rewrite below).
 * - Production (compose/Caddy): leave it UNSET and calls go to the relative
 *   `/api/*` prefix — Caddy strips it and proxies to backend:8000, so the
 *   browser never needs to resolve the internal `backend` hostname.
 */

const DIRECT = process.env.NEXT_PUBLIC_BACKEND_URL || undefined;
const PREFIX = DIRECT ?? "/api";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${PREFIX}${path}`, init);
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status} ${detail}`);
  }
  return res.json() as Promise<T>;
}

export interface Health {
  status: string;
  documents_count: number;
  chunks_count: number;
  eval_runs_count: number;
  environment: string;
  llm_backend: string;
}

export interface DocumentInfo {
  doc_id: string;
  title: string;
  source_path: string | null;
  chunk_count: number;
  ingested_at: string | null;
}

export interface PublicConfig {
  environment: string;
  llm_backend: string;
  generation_model: string | null;
  judge_backend: string;
  judge_model: string;
  embedding_model: string;
  reranker_model: string;
  retrieval_top_k: number;
  rerank_top_n: number;
  rrf_k: number;
  compression_threshold: number;
  max_context_tokens: number;
}

export interface Citation {
  chunk_id: string;
  doc_title: string;
  snippet: string;
  source_path: string | null;
}

export interface RetrievalHit {
  chunk_id: string;
  score: number;
  text_preview: string;
}

export interface QueryResponse {
  answer: string;
  citations: Citation[];
  retrieval_debug: {
    bm25_hits: RetrievalHit[];
    vector_hits: RetrievalHit[];
    fused_order: RetrievalHit[];
    reranked_order: RetrievalHit[];
  };
}

export interface EvalScores {
  faithfulness: number | null;
  answer_relevancy: number | null;
  context_precision: number | null;
  context_recall: number | null;
}

export interface EvalRunSummary {
  run_id: string;
  retrieval_mode: string;
  timestamp: string;
  scores: EvalScores;
}

export interface QuestionScore extends EvalScores {
  question: string;
  answer: string;
}

export interface EvalRunResponse {
  run_id: string;
  retrieval_mode: string;
  timestamp: string;
  scores: EvalScores;
  per_question_breakdown: QuestionScore[];
}

export interface IngestResponse {
  doc_id: string;
  title: string;
  chunk_count: number;
  sample_chunks: {
    chunk_id: string;
    text_preview: string;
    token_count: number;
    section_header: string | null;
  }[];
}

export const api = {
  health: () => req<Health>("/health"),
  documents: () => req<DocumentInfo[]>("/documents"),
  config: () => req<PublicConfig>("/config"),

  query: (question: string, mode = "hybrid", top_k = 5) =>
    req<QueryResponse>("/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, mode, top_k }),
    }),

  ingestFile: (file: File, title: string) => {
    const form = new FormData();
    form.append("file", file);
    form.append("title", title || file.name);
    return req<IngestResponse>("/ingest", { method: "POST", body: form });
  },

  ingestText: (title: string, raw_text: string) => {
    const form = new FormData();
    form.append("title", title);
    form.append("raw_text", raw_text);
    return req<IngestResponse>("/ingest", { method: "POST", body: form });
  },

  evalRuns: () => req<EvalRunSummary[]>("/eval/runs"),
  evalRun: (qa_set_name: string, mode: string) =>
    req<EvalRunResponse>("/eval/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ qa_set_name, mode }),
    }),
  scorecard: (run_id: string) =>
    req<Record<string, unknown>>(`/eval/runs/${run_id}`),
  compare: (run_id_1: string, run_id_2: string) =>
    req<Record<string, unknown>>(
      `/eval/compare?run_id_1=${run_id_1}&run_id_2=${run_id_2}`,
      { method: "POST" },
    ),
};
