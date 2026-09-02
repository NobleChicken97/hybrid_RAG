"""Retrieval-stage diagnostic: where does ground-truth evidence get lost?

For each QA question, runs vector+BM25 -> RRF -> rerank -> compression and
checks keyword overlap between the ground-truth answer and:
  1. the top-20 fused candidate pool (retrieval coverage)
  2. the top-5 reranked chunks (rerank selection)
  3. the compressed context (compression)

No LLM calls; safe to run alongside an eval.
"""
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

from app.config import get_settings
from app.evaluation.qa_loader import load_qa_set
from app.ingestion.embedder import embed_query
from app.retrieval import vector_store, bm25_index
from app.retrieval.fusion import fuse
from app.retrieval.reranker import rerank
from app.retrieval.compressor import compress_context

STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "to", "of", "in", "on", "for", "with", "and", "or", "not", "no",
    "it", "its", "this", "that", "these", "those", "as", "at", "by",
    "from", "you", "your", "use", "used", "using", "should", "can",
    "will", "would", "do", "does", "did", "how", "what", "why", "when",
    "which", "each", "any", "all", "more", "most", "other", "than",
    "then", "so", "such", "into", "over", "under", "out", "up", "down",
}


def keywords(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if len(w) > 2 and w not in STOPWORDS}


def overlap(gt: str, texts: list[str]) -> tuple[float, set[str]]:
    """Fraction of ground-truth keywords covered, and the missing ones."""
    gt_kw = keywords(gt)
    if not gt_kw:
        return 1.0, set()
    corpus_kw = keywords(" ".join(texts))
    missing = gt_kw - corpus_kw
    return 1.0 - len(missing) / len(gt_kw), missing


def main() -> None:
    qa_items = load_qa_set("default")
    settings = get_settings()
    print(f"[Diag] {len(qa_items)} questions | top_k={settings.retrieval_top_k} "
          f"top_n={settings.rerank_top_n} | compression_threshold={settings.compression_threshold}\n")

    rows = []
    for i, qa in enumerate(qa_items, 1):
        q_emb = embed_query(qa.question)
        vector_results = vector_store.search(q_emb, top_k=settings.retrieval_top_k)
        bm25_results = bm25_index.search(qa.question, top_k=settings.retrieval_top_k)
        fused = fuse(
            bm25_results=[(r.chunk_id, r.score, r.text) for r in bm25_results],
            vector_results=[(r.chunk_id, r.score, r.text) for r in vector_results],
            k=settings.rrf_k,
        )
        candidates = [(r.chunk_id, r.text, r.sources) for r in fused]
        reranked = rerank(qa.question, candidates[: settings.retrieval_top_k], top_n=settings.rerank_top_n)
        compressed = compress_context(qa.question, [(r.chunk_id, r.text) for r in reranked])

        pool_texts = [t for _, t, _ in candidates]
        rerank_texts = [r.text for r in reranked]
        comp_texts = [c.compressed_text for c in compressed]

        cov_pool, miss_pool = overlap(qa.ground_truth_answer, pool_texts)
        cov_rerank, miss_rerank = overlap(qa.ground_truth_answer, rerank_texts)
        cov_comp, miss_comp = overlap(qa.ground_truth_answer, comp_texts)

        # Localize the loss stage
        if cov_comp >= 0.999:
            stage = "OK"
        elif cov_rerank > cov_comp:
            stage = "COMPRESSION"
        elif cov_pool > cov_rerank:
            stage = "RERANK"
        else:
            stage = "RETRIEVAL"

        rows.append((qa.question, cov_pool, cov_rerank, cov_comp, stage))
        print(f"{i:2d}. [{stage:11s}] pool={cov_pool:.2f} rerank={cov_rerank:.2f} compressed={cov_comp:.2f} "
              f"| {qa.question[:60]}")
        if stage != "OK":
            print(f"    missing after compression: {sorted(miss_comp)[:12]}")

    n_ok = sum(1 for r in rows if r[4] == "OK")
    print(f"\n[Diag] Full evidence survived all stages: {n_ok}/{len(rows)}")
    from collections import Counter
    print(f"[Diag] Loss stages: {dict(Counter(r[4] for r in rows))}")


if __name__ == "__main__":
    main()
