# instructions.md — Multi-Backend LLM Integration for Project 01 (Hybrid RAG)

This is a supplement to `Project1_Hybrid_RAG_MASTER_GUIDE.md`. It covers ONLY the
model-backend piece: why it exists, which models to use, how to wire it up, how
to test it, and how to deploy it without breaking anything.

---

## 1. Why this exists

The Claude API costs money for high call volume, and Google's Gemini free tier
returns `429 GenerateContentInputTokensPerModelPerMinute-FreeTier` almost
instantly once you start running batches of queries (the eval harness fires
several LLM calls back-to-back, each with multiple retrieved chunks in the
prompt — that burns the per-minute input-token quota fast).

The fix is to never depend on one provider. Build the generation step as a
swappable backend, default to a free local model for all day-to-day dev work,
and only reach for a cloud API when you actually need to (the deployed demo,
or a quality A/B comparison).

---

## 2. Final model list

| Role                                      | Model                                          | Runs where            |
| ----------------------------------------- | ---------------------------------------------- | --------------------- |
| Embeddings                                | `BAAI/bge-small-en-v1.5`                     | Local, CPU            |
| Reranker                                  | `cross-encoder/ms-marco-MiniLM-L-6-v2`       | Local, CPU            |
| Generation — local default               | `qwen3:4b`(Ollama)                           | Local, GPU (4GB VRAM) |
| Generation — local A/B backup            | `phi4-mini:3.8b`(Ollama)                     | Local, GPU (4GB VRAM) |
| Generation — cloud default (deploy)      | `gpt-oss-120b`via**Cerebras**          | Cloud, free           |
| Generation — cloud fallback              | `llama-3.3-70b-versatile`via**Groq**   | Cloud, free           |
| Generation — quality fallback (optional) | Claude Haiku                                   | Cloud, paid           |
| **RAGAS judge model**               | `gpt-oss-120b`via Cerebras (or Claude Haiku) | Cloud                 |

> **Cerebras account reality (verified June 2026):** `llama-3.3-70b` is NOT
> available on the personal free tier. Only two models exist on this account:
> `gpt-oss-120b` (Production, 65,536 ctx) and `zai-glm-4.7` (Preview, 64,000 ctx).
> Use `gpt-oss-120b` for everything — generation and judging.
>
> **Cerebras free-tier rate limits (personal account):**
> Requests: 5/min · 150/hr · 2,400/day | Tokens: 30K/min · 1M/hr · 1M/day
> → At 5 RPM, add `time.sleep(13)` between calls in the eval harness loop to
> avoid 429s. Daily caps are generous enough for all dev work.
>
> **Groq note:** The rate limit table in the Groq docs shows *Developer Plan*
> numbers, not free tier. Go to console.groq.com → Settings → Limits to see
> your actual free-tier per-model quotas before planning around them.
> `llama-3.3-70b-versatile` is confirmed live on Groq as a production model.

**Hard rule:** never use `qwen3:4b` or `phi4-mini` as the RAGAS judge. They're
fine for *generating* answers, not reliable enough for *grading* them. The
judge model is a separate config slot from the generation model — you can
judge a Qwen3-generated answer with a Cerebras-hosted judge in the same run.

---

## 3. Architecture (the one rule that matters)

Everything upstream — loader, chunker, embeddings, BM25, fusion, reranker,
compression — stays identical no matter which LLM answers the question. The
only swappable part is one function:

```
generate(prompt: str, backend: str) -> str
```

`backend` is read from an environment variable, never hardcoded, never chosen
inside business logic. One function, one switch statement, done.

---

## 4. Setup TODO checklist

### Phase A — Local Ollama setup (do this first, it's free and instant)

* [ ] Install Ollama
* [ ] `ollama pull qwen3:4b`
* [ ] `ollama pull phi4-mini`
* [ ] Confirm both respond: `ollama run qwen3:4b "say hello"` and same for phi4-mini
* [ ] Note the local endpoint: `http://localhost:11434` (OpenAI-compatible at `/v1`)

### Phase B — Cloud backend accounts

* [ ] Sign up for a Cerebras API key at https://cloud.cerebras.ai (no credit card)
  → Available models on personal/free tier: `gpt-oss-120b` (Production) and
  `zai-glm-4.7` (Preview). `llama-3.3-70b` is NOT available — use `gpt-oss-120b`.
* [ ] Sign up for a Groq API key at https://console.groq.com (no credit card)
  → Check your actual free-tier rate limits at console.groq.com → Settings → Limits.
  The model docs show Developer Plan limits, not free tier.
* [ ] (Optional) Get an Anthropic API key if you want the Claude Haiku
  quality-fallback option for demo footage
* [ ] Store all keys in a local `.env` file — never commit this file

### Phase C — Backend abstraction layer

* [ ] Define the env vars (see Section 6 for the full list)
* [ ] Write `generate(prompt, backend)`:
  * `ollama_qwen3` / `ollama_phi4mini` → call `http://localhost:11434/v1/chat/completions`
    with the right model name
  * `cerebras` → call Cerebras' OpenAI-compatible endpoint with `CEREBRAS_API_KEY`
  * `groq` → call Groq's OpenAI-compatible endpoint with `GROQ_API_KEY`
  * `claude` → call Anthropic API with `ANTHROPIC_API_KEY`
* [ ] Wrap every branch in a try/except. If an Ollama call fails because the
  local server isn't reachable, raise a clear
  `"Local model unavailable in this environment"` error — don't let it
  hang or time out silently
* [ ] Add a single retry-with-backoff wrapper around all cloud calls (you
  already need this per Project 02's reliability requirements — reuse it
  here too)

### Phase D — Eval harness, multi-backend comparison

* [ ] Add `generation_backend` and `judge_backend` fields to the `EvalRun`
  `config_snapshot` (you already have this field — just populate it)
* [ ] Run the full held-out QA set through `ollama_qwen3`
* [ ] Run it again through `ollama_phi4mini`
* [ ] Run it again through `cerebras` (or whichever cloud backend you'll
  deploy with)
  → **IMPORTANT:** Cerebras free tier = 5 RPM. Add `time.sleep(13)` between
  calls in the harness loop or you'll 429 almost immediately on any batch
  of 20+ questions. Daily cap (2,400 req / 1M tokens) is fine for dev.
* [ ] Use the SAME judge backend (Cerebras `gpt-oss-120b` or Claude Haiku) to
  score all three runs — this is what makes the comparison fair
* [ ] Save all three scorecards, put the comparison table in your README

### Phase E — Environment-aware UI

* [ ] Add an `ENVIRONMENT=local|production` env var
* [ ] In the Streamlit model picker, only list `ollama_qwen3` /
  `ollama_phi4mini` when `ENVIRONMENT=local`
* [ ] Always list `cerebras` / `groq` / `claude` regardless of environment

---

## 5. Testing checklist

* [ ] Each backend independently returns a coherent answer for the same test
  question (run all 5 manually once, side by side)
* [ ] Killing the local Ollama process and calling `generate()` with
  `ollama_qwen3` returns the clear error message, not a hang or a crash
* [ ] Setting `LLM_BACKEND=cerebras` with no Ollama running at all still works
  end-to-end (proves the deployed path doesn't secretly depend on Ollama)
* [ ] The Streamlit dropdown shows only cloud options when
  `ENVIRONMENT=production`
* [ ] Three separate `EvalRun` rows exist after Phase D, each tagged with the
  correct `generation_backend`, and all three share the same
  `judge_backend`
* [ ] A simulated Cerebras failure (wrong API key) correctly triggers the
  retry/backoff, then a clean failure — not a silent wrong answer

---

## 6. Environment variables — quick reference

```
ENVIRONMENT=local                 # or: production
LLM_BACKEND=ollama_qwen3          # ollama_qwen3 | ollama_phi4mini | cerebras | groq | claude
RAGAS_JUDGE_BACKEND=cerebras      # cerebras | claude  (never a local 4B model)

OLLAMA_HOST=http://localhost:11434

# Cerebras — personal free tier has only: gpt-oss-120b, zai-glm-4.7
# llama-3.3-70b is NOT available on the personal plan (deprecated for this account)
CEREBRAS_MODEL=gpt-oss-120b
CEREBRAS_API_KEY=...

# Groq — llama-3.3-70b-versatile is confirmed live as a production model
# Check console.groq.com → Settings → Limits for YOUR actual free-tier quotas
# (the docs table shows Developer Plan numbers, which are higher)
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_API_KEY=...

ANTHROPIC_API_KEY=...             # optional
```

---

## 7. Deployment checklist (Render/Railway free tier)

* [ ] Do NOT install Ollama on the host — it won't fit in free-tier RAM anyway
* [ ] Set `ENVIRONMENT=production` in the platform's dashboard
* [ ] Set `LLM_BACKEND=cerebras` (primary) — model string is `gpt-oss-120b`,
  the only production model on the personal free tier. Switch to `groq`
  (`llama-3.3-70b-versatile`) if Cerebras hits rate limits or changes catalog.
* [ ] Set `RAGAS_JUDGE_BACKEND=cerebras` (or `claude` if you added the key)
* [ ] Confirm the deployed app never even attempts to reach
  `http://localhost:11434` — check logs on first boot to be sure
* [ ] Re-run the full eval harness once against the deployed config before
  calling it "done," not just locally

---

## 8. What NOT to do

* Don't hardcode a provider's model name as a permanent dependency — free
  catalogs (Cerebras, Groq, OpenRouter) change without notice. Cerebras already
  dropped `llama-3.3-70b` from the personal tier; the current production model
  is `gpt-oss-120b`. Keep the model string in config (env var), not in code.
* Don't use the same small local model as both generator and judge — it makes
  your RAGAS scores unreliable in a way that's hard to notice until you
  compare against a real judge later.
* Don't skip Phase E (environment-aware UI) and just hope nobody clicks the
  Ollama option in production — guard it in code, not by convention.
