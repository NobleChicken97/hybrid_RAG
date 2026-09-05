# Interview Prep Guide — Eli Lilly, Software Engineer
### Built around one project: the Hybrid RAG System (live at https://rag.noblechicken.me)

> **How to use this guide.** Every topic has two versions. **Say it simple** = the idea in plain words (use when they ask "explain it like I'm new to this", or to open an answer before going deep). **Interview-ready** = the same idea in first person, with specifics, numbers, and judgment — this is the voice to use for 80% of the interview. Memorize the numbers in Section 13 cold.

---

## 1. The 60-second pitch (open with this when they say "tell me about a project")

**Say it simple.** I built a question-answering system over documents. You upload files, ask questions in plain English, and it answers with citations showing exactly which paragraphs the answer came from — plus a dashboard that scores how good the answers are.

**Interview-ready.** "I designed and shipped a production hybrid-retrieval RAG system. It ingests PDF, Markdown, and text, retrieves with BM25 plus vector search fused by reciprocal rank fusion, reranks with a cross-encoder, compresses context, and generates cited answers. Around it I built a RAGAS evaluation harness, a six-route Next.js console, and a full AWS deployment with CI/CD. It's live today with a measured scorecard — faithfulness 0.89, recall 1.0 on a 20-question held-out set — and every claim on the site traces to a real pipeline output."

---

## 2. What the app is

**Say it simple.** Think of a very honest librarian. Normal chatbots answer from memory and sometimes make things up. Mine refuses to do that: it first finds the relevant pages in your documents, then answers only from those pages, and shows you the exact paragraphs as citations. A second system then grades the answers automatically, so quality is a number, not a feeling.

**Interview-ready.** "It's a retrieval-augmented generation system with an embedded evaluation harness. The product loop is ingest → ask → evaluate: documents become overlapping chunks with BGE embeddings in ChromaDB plus a BM25 keyword index; questions run both retrievers in parallel, fuse with RRF, rerank the top candidates with BAAI/bge-reranker-base, compress to budget, and generate with Gemini flash-lite, grounding every claim in citations resolved to chunk IDs. The differentiator is the eval loop — four RAGAS metrics over a 20-question held-out set, saved per run, comparable across runs — so retrieval changes are decided by measurement, not vibes."

---

## 3. Architecture and request flows

### 3.1 The query flow (they WILL ask "walk me through what happens when I ask a question")

**Say it simple.** Your question goes two places at once: a keyword search (like Ctrl+F, but smart about word importance) and a meaning search (finds paragraphs about the same idea even with different words). The two result lists get merged fairly, a specialist model re-orders the merged list by actual relevance, the text gets trimmed to fit, and the language model writes an answer using only that text — attaching a footnote number to each claim.

**Interview-ready.** "The question fans out to `vector_store.search` with a BGE-small embedding and `bm25_index.search` in parallel, each returning top-20. `fusion.py` merges them with reciprocal rank fusion, k=60, so a chunk ranking high in either source surfaces without score normalization hacks. The fused pool goes to the cross-encoder reranker, top-5 survive. `compressor.py` is budget-conditional — under 2,000 tokens the context passes through untouched; over budget, sentences below a 0.3 cross-encoder threshold are dropped. Generation uses Gemini flash-lite with citation instructions, and `citations.py` resolves each `[n]` marker to a chunk ID, title, and snippet. `retrieval_debug` — BM25 hits, vector hits, fused order, reranked order — ships back with every response, which is what powers the Topology page."

### 3.2 The ingest flow

**Say it simple.** Upload a file or paste text. The system splits it into overlapping paragraphs, converts each into a numeric fingerprint capturing its meaning, stores fingerprints in one database and keywords in another, and guards against indexing the same document twice.

**Interview-ready.** "Ingestion runs a context-aware chunker — headers, then paragraphs, then a size cap, so chunk boundaries respect document structure — then embeds with BAAI/bge-small-en-v1.5 (384-dim) into ChromaDB while rank_bm25 builds the keyword index, with metadata in SQLite. A content-hash duplicate guard returns 409 on re-ingest; that guard exists because a PDF uploaded twice once double-indexed a corpus early on. Sample chunk previews return in the response so the UI can show what was indexed."

### 3.3 The eval flow

**Say it simple.** We keep 20 questions with known-correct answers locked away. After any pipeline change, the system answers all 20 and an automated judge scores each answer on four axes: truthfulness, relevance, whether the retrieved paragraphs were on-point, and whether any needed evidence was missed.

**Interview-ready.** "The harness runs the full pipeline per QA pair and scores with RAGAS 0.4: faithfulness, answer relevancy, context precision, context recall. Two deliberate design points: failed generations are excluded from aggregates instead of scored as zero — scoring an API outage as an answer once invalidated an entire baseline — and the judge backend is explicit per run (Gemini or Groq via LangChain wrappers), recorded in the run row alongside the corpus state. Runs persist to SQLite with per-question breakdowns, and `/eval/compare` diffs two runs metric by metric."

---

## 4. Routes reference (know all six + the API)

**Say it simple.** Six pages: home with live stats, ask questions, upload documents, run and compare evaluations, inspect the system's health and settings, and trace exactly which paragraphs any answer came from.

**Interview-ready.** "Six App Router routes over one typed client (`lib/api.ts`): `/` overview (live health stats, corpus meters, latest-audit board), `/ask` (question + mode + top-K, answer, citations, full retrieval debug), `/ingest` (file upload or raw text with chunk previews), `/eval` (run evaluations, past-runs table, two-run comparison), `/system` (config snapshot with zero secrets, document table), `/topology` (the real retrieval path per question — reranked chunks with cross-encoder scores, cited ones badged). API mirrors it: `POST /ingest`, `POST /query`, `POST /eval/run` (token-gated in prod), `GET /eval/runs[/{id}]`, `POST /eval/compare`, `GET /health|/documents|/config`. The web talks same-origin `/api/*` — Caddy strips the prefix and proxies to the backend, so the browser never resolves internal hostnames."

---

## 5. Tech stack — every choice, with the why

| Layer | Choice | Why it (and not the alternative) |
|---|---|---|
| Backend | FastAPI (Python 3.11) | Async, auto OpenAPI docs at `/docs`, trivial to instrument. Express would've split the ML ecosystem in half — every embedding/rerank library here is Python-first. |
| Embeddings | BAAI/bge-small-en-v1.5, 384-dim | CPU-runnable, no GPU bill, strong retrieval quality per dollar (free). OpenAI embeddings would add per-call cost and a network dependency to the hottest path. |
| Vector store | ChromaDB (local, persistent) | Zero infra, survives restarts on disk. Managed Pinecone/Weaviate would erase the "runs anywhere on CPU" design point for a 234-chunk corpus. |
| Keyword search | rank_bm25 (pure Python) | No service, no index server. Complements vectors exactly where they fail: rare terms, IDs, exact phrases. |
| Fusion | RRF, k=60 | No score normalization between incompatible scoring systems; the standard constant. |
| Reranker | BAAI/bge-reranker-base (MiniLM fallback) | Won a benchmarked A/B (below). Costs ~1.1 GB disk and slower CPU rerank — accepted for +6.6 precision. |
| Generation | Gemini flash-lite (Groq gpt-oss-120b fallback) | Free tier; flash-lite has the bigger daily bucket. Flash proper 503'd on high demand, so flash-lite is permanent. Dual backends ended single-provider fragility. |
| Eval | RAGAS 0.4 + LangChain wrappers | Industry-standard RAG metrics; explicit judge LLM per run. Custom scoring would be uncalibrated opinion. |
| Metadata | SQLite + SQLAlchemy | Zero-config, file-backed, joins trivially with the deployment's volume story. Postgres would be ceremony for one box. |
| Frontend | Next.js 16 + React 19 + Tailwind v4 + shadcn | Real routes with live data (Streamlit retired — below); shadcn Base-UI primitives for tables/buttons/badges instead of hand-rolled. |
| Reverse proxy/TLS | Caddy | Automatic Let's Encrypt, 5-line config. Nginx would've meant certbot sidecars. |
| Deploy target | Lightsail 4 GB (~$24/mo flat) | Decision record below. |
| Images/registry | Docker + ECR, keep-3 lifecycle | Reproducible builds; lifecycle caps the multi-GB backend image cost. |
| CI/CD | One GitHub Actions pipeline file | Lint + gitleaks + pytest + gated build/push/deploy; serialized with a concurrency group after a real race incident. |

---

## 6. Decision log — X over Y, with pros and cons (interview gold)

**Hybrid retrieval over vector-only.** Pro: measured wins — relevancy +5.3, recall +5.3 with every evidence span captured. Con: −1.1 precision (top-5 carries slightly more non-evidence text) and two moving systems to operate. Verdict: the recall gain dominates for a citations product — a missing citation is worse than a slightly noisier context.

**bge-reranker-base over ms-marco-MiniLM.** Pro: precision 0.857→0.924, fixed the Q14 ranking failure at rank 1 instead of 8, tiny faithfulness/relevancy costs (−0.02/−0.03). Con: ~1.1 GB weights, slower CPU rerank. Decided by a full A/B (capture-rank analysis + two clean RAGAS arms), not by vibes.

**Gemini flash-lite over flash.** Pro: actually available — flash 503'd on high demand even with a fresh key, and the free tier caps at 20 req/day. Con: marginally weaker model. Availability beats benchmarks you can't call.

**Lightsail 4 GB over Vercel / EC2 / Fargate.** Vercel rejected: serverless has no persistent disk (ChromaDB, BM25, SQLite all break) and can't host long-lived processes. EC2 t3.medium was runner-up (more control, credit-billing complexity). Fargate was orchestration theater for one box. Lightsail won on flat pricing and a static IP.

**Next.js over Streamlit.** Pro: real routes, typed client, production build, Caddy-friendly. Con: a rewrite of a working UI. Trigger: Streamlit served disconnected demo data and couldn't be the evidence console the product needed.

**ECR + GH Actions CD over manual SSH deploys.** Pro: pinned SHA images, health-gated, one-click rollback. Con: ~$3–5/mo storage, 12-minute builds. Worth it the week manual deploys collided mid-restart (lesson logged, concurrency guard added).

**EVAL_TOKEN shared secret over open endpoint.** The eval endpoint burns ~100 LLM calls per hit — leaving it public was an open wallet. Chose a header secret (empty = open locally, required in prod) over full auth: proportional security for a demo console.

**`run_in_threadpool` for evals.** RAGAS runs nested async that crashes on uvloop; local script runs never saw it because scripts have no outer loop. Threadpool matches script conditions exactly — plus stops 10-minute evals blocking the event loop.

**SQLite/Chroma/BM25 files over managed services.** See stack table. Consciously boring storage so all novelty budget went into retrieval quality.

---

## 7. Problems faced → diagnosis → fix (STAR stories — pick 2–3 to tell)

**Story 1 — "The compressor was destroying evidence."** Situation: context_recall sat at 0.4 while retrieval coverage was fine. Task: find where evidence died. Action: built a stage-by-stage diagnostic tracing ground-truth keywords through pool → rerank → compression; it showed sentence-level compression shredding evidence on 13/20 questions. Result: made compression budget-conditional (pass-through under token budget) — recall went to 0.95–1.0 with zero retrieval changes. *Shows: instrument before optimizing; the bottleneck is rarely where you assume.*

**Story 2 — "Two stacked null-eval mysteries in production."** Situation: first prod eval returned 20 good answers and zero scores. Action: backend logs showed a uvloop nested-loop crash (fixed with threadpool offload + regression test). Re-ran — still null, no crash. Dug again: the judge model name still said Gemini while the backend was Groq — 80 silent 404s. Fixed the name, third run scored 0.89/0.93/0.91/1.0. *Shows: sequential debugging, reading logs before theorizing twice, and keeping null runs as evidence.*

**Story 3 — "The deploy that took down prod."** Situation: a manual restart collided with a CD deploy mid-container-recreate; backend vanished, API 502s. Action: diagnosed the name-conflict race from both logs, recovered with a clean reconcile, then added a pipeline-wide concurrency queue plus a standing rule. *Shows: incident ownership, blameless root-cause, systemic prevention.*

**More in reserve (one-liners):** Q14 rerank miss → proved MiniLM's weakness with capture-rank data, upgraded via A/B; quota exhaustion → Groq fallback + retry/backoff policy; duplicate-indexed PDF → content-hash guard + corpus dedupe (195 chunks); flaky smoke test → self-seeding fixture; grid-blowout UI overflow → `min-w-0` + `break-all` hardening.

---

## 8. Mentality and methodology (when they ask "how do you work")

**Say it simple.** Measure first, guess never. Write down decisions with reasons. Test the real thing, not a copy of it. Docs are part of the product, updated the same day as the code.

**Interview-ready.** "Four habits: (1) evidence-first — every retrieval change ships with a RAGAS number or it doesn't ship; (2) verify by execution — I re-run suites, probe live endpoints, and read logs rather than trusting reasoning; (3) decide in writing — the repo carries decision records with pros, cons, and the data that settled each one; (4) small reversible steps — feature flags, fallbacks, and rollback paths before heroics. I also use AI coding agents as force multipliers, but under verification discipline: every generated change must pass the same tests, lint, logs, and live checks as a hand-written one."

---

## 9. Key learnings (honest, specific)

- Retrieval quality is a measurement problem before it's a modeling problem — the diagnostic harness paid for itself ten times over.
- Failure handling IS the feature: failure-exclusion in scoring, retry/backoff, dual LLM backends, duplicate guards — robustness work was half the project.
- Free tiers are load-bearing constraints, not free lunches: quota math (20/day Gemini, ~100 calls/eval) drove real architecture (Groq fallback, judge-backend switching).
- Dev/prod parity bites hardest at the seams: uvloop only exists under the server, ECR auth expires in 12h, ports differ per machine — each got a structural answer, not a sticky note.
- conciseness in docs beats completeness: surgical doc edits stay current; rewrites rot.

---

## 10. Mapping yourself to the JD (use their words back)

- **"Vivid learner, experiment without fear of failure"** → "I benchmarked two rerankers end-to-end, ran retrieval experiments that returned nulls twice in production, and kept the nulls as evidence. Experimentation with instrumentation."
- **"CS concepts and SDLC"** → SDLC end-to-end solo: requirements (decision records), design (pipeline architecture), implementation, testing (61 tests + live probes), deployment (Docker/ECR/Lightsail), maintenance (incident response, monitoring via health + eval trends). Name the cycle explicitly.
- **"Willingness to learn any technology across the spectrum"** → one project touched: full-stack (FastAPI + Next.js), Cloud (AWS Lightsail/ECR/IAM), Data (ChromaDB, SQLite, embeddings), InfoSec (secret hygiene, least-privilege IAM, endpoint gating, gitleaks), DevOps (Docker, GH Actions, Caddy/TLS), UI/UX (five design iterations against real user feedback). Say: "I go where the bottleneck is."
- **"Reasoning, attention to detail, analytical ability"** → the compression diagnosis, the Q14 capture-rank analysis, the double null-eval root-causing. Details: k=60, top-5, 0.3 threshold — precision signals care.
- **"Interpersonal skills, dispersed teams"** → be honest about solo scope, then pivot: "I collaborated async across time zones with a domain stakeholder" — only if true. Otherwise: "I document so well that async collaboration is frictionless — decision records, runbooks, evidence-linked todos — which is exactly the skill distributed teams run on." (True and checkable: offer to show the repo.)
- **"Assemble, share, apply learnings"** → "Every incident became a regression test, a doc entry, or a guardrail — the eval-guard, the dedupe guard, the CD concurrency rule all started as failures."
- **"Self-starter, can-do"** → "Scoped, built, deployed, and operated this solo to a live URL with a public scorecard — no ticket queue involved."
- **"Think differently, prototype, productize"** → "The retrieval-debug Topology page started as a one-off diagnostic script and became a product surface. Prototype → evidence → product is my default loop."

---

## 11. Why you beat peers + what Lilly gets

**Say it simple.** Most candidates show tutorial projects. Mine is live, measured, and has survived real failures — with the receipts (scorecards, incident logs, decision records) to prove every claim in the interview itself.

**Interview-ready.** "Three separations: (1) production proof, not screenshots — live URL, real users-possible, CI/CD, TLS, monitoring-by-eval; (2) measurement culture — I don't claim quality, I publish it per run and can explain every delta; (3) operational maturity — quota engineering, secret hygiene, incident response, rollback paths. What Lilly gets is someone who prototypes fast *and* productizes completely: the same person who spikes a reranker A/B on Monday writes the runbook, the regression test, and the rollback plan by Friday — across cloud, data, security, and UI without waiting for permission."

**Lilly alignment (say it once, confidently).** "Lilly builds systems where correctness has consequences — a wrong answer in pharma isn't a bad demo, it's a patient-safety issue. That's why I built a system whose entire identity is grounded, cited, evaluated answers: faithfulness as a first-class metric, failures excluded instead of hidden, evidence preserved end-to-end. The engineering culture transfers directly."

---

## 12. Non-project prep (the JD tests breadth — don't get blindsided)

**CS quick-fire (one-line answers to rehearse):** REST = stateless resource verbs + status codes; SQL vs NoSQL = relations/integrity vs scale/flexibility; indexing = B-tree trade of write cost for read speed; TCP vs UDP = reliable-ordered vs fast-lossy; DNS = hierarchical name resolution with caching/TTLs; HTTPS = TLS handshake then symmetric session; hashing vs encryption (one-way vs reversible); Big-O of your pipeline stages (retrieval top-k, rerank linear in candidates — which is WHY top_n=5 matters); processes vs threads vs async (know which your eval fix used and why); CAP theorem one-liner; idempotency (your 409 duplicate guard IS the example — use it!).

**InfoSec basics (JD names it twice):** least privilege (your IAM policy scoped to two ECR repos), secrets hygiene (env files gitignored, gitleaks in CI, header-gated eval endpoint), OWASP top-3 awareness (injection, broken auth, sensitive exposure — map each to something you did), TLS everywhere (Caddy/ACME), dependency risk (`pip check` conflicts you knowingly documented).

**SDLC/Agile/DevOps:** be able to narrate YOUR SDLC in their vocabulary (plan → design → implement → test → deploy → monitor), Agile ceremonies in one line each, CI vs CD (yours: test-gated CD with pinned SHAs), trunk-based development, what a rollback plan contains.

**Behavioral bank (STAR each, 2 minutes max):** conflict/disagreement, missed deadline, ambiguous requirements, learning something fast, helping someone else succeed, a failure that taught you, working with difficult constraints (quota/budget examples ready-made), why Lilly, why this role, where you want to grow (name a real gap + your plan to close it — e.g., "distributed systems at scale; my system is single-box by design, and I want to learn sharded retrieval").

**Questions to ask THEM (shows senior thinking):** "How does the team measure production quality — evals, SLOs, or review?" / "What's the path from prototype to production here, and where do prototypes usually die?" / "How are on-call and incident learnings handled?" / "What does good look like in the first 90 days?"

---

## 13. Cheat sheet — numbers to memorize cold

- Corpus: **3 docs, ~234 chunks** prod · QA set: **20 questions** · Suite: **61 tests**, ruff clean
- Retrieval: top-20 each arm · **RRF k=60** · rerank **top-5** · compression: pass-through under **2,000 tokens**, else **0.3** threshold
- Models: **bge-small-en-v1.5 (384d)** → **bge-reranker-base** → **gemini flash-lite** (Groq gpt-oss-120b fallback + judge)
- Local hybrid: **1.0 / 0.9502 / 0.8571 / 1.0** · vector-only: 1.0 / 0.897 / 0.868 / 0.947
- bge A/B arm: **0.9778 / 0.9160 / 0.9235 / 1.0** (precision +6.6 vs baseline)
- Prod Groq run `eval_3ad9de1e`: **0.8897 / 0.9277 / 0.9083 / 1.0**
- Live: **rag.noblechicken.me** · Lightsail 4 GB **~$24/mo** · Caddy TLS · ECR keep-3 · single-file pipeline CI/CD
- Incidents: null evals ×2 (uvloop + judge-name), CD race, quota walls, double-indexed PDF (195 dup chunks removed)

*Good luck. You built the thing, you measured the thing, you operated the thing — now just tell the truth about it, with numbers.*
