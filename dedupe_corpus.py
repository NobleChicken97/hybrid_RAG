"""One-shot corpus dedup: remove the double-ingested gatsby PDF and backfill
content hashes for the surviving documents.

Observed 2026-09-02: `the-great-gatsby.pdf` was ingested twice (2026-06-22),
so one copy's chunks are duplicate index entries. This script:
  1. Deletes the second copy from ChromaDB, BM25, and SQLite (EvalRuns kept).
  2. Backfills documents.content_hash by re-extracting text from the files in
     sample_docs/ (so the new duplicate guard also protects legacy documents).

Idempotent: exits cleanly if the duplicate is already gone.
Run AFTER any eval that needs the original corpus (scorecard comparability).
"""
import sys

sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import text as sql_text  # noqa: F401  (kept for potential raw queries)

from app.config import get_settings
from app.database import get_engine, get_session_factory, Document, Chunk
from app.ingestion.loader import load_document
from app.retrieval import vector_store, bm25_index

# doc_c74bd5716030 kept (first gatsby ingest), doc_6974ad192700 removed.
DUPLICATE_DOC_ID = "doc_6974ad192700"

SURVIVORS = [  # (doc_id prefix, sample_docs file, title)
    ("doc_ff0788787cf1", "sample_docs/sample_fastapi.md"),
    ("doc_99860513de40", "sample_docs/sample_python_guide.md"),
    ("doc_c74bd5716030", "sample_docs/the-great-gatsby.pdf"),
]


def main() -> None:
    SessionLocal = get_session_factory()
    db = SessionLocal()

    # --- 1. Remove the duplicate document ---
    dup = db.query(Document).filter(Document.doc_id == DUPLICATE_DOC_ID).first()
    if dup is None:
        print(f"[Dedupe] {DUPLICATE_DOC_ID} already removed — nothing to delete.")
    else:
        n_vec = vector_store.delete_document(DUPLICATE_DOC_ID)
        n_bm25 = bm25_index.remove_document(DUPLICATE_DOC_ID)
        db.query(Chunk).filter(Chunk.doc_id == DUPLICATE_DOC_ID).delete()
        n_sql = db.query(Document).filter(Document.doc_id == DUPLICATE_DOC_ID).delete()
        db.commit()
        print(f"[Dedupe] Removed duplicate {DUPLICATE_DOC_ID}: "
              f"chroma={n_vec} bm25={n_bm25} sqlite_docs={n_sql}")

    # --- 2. Backfill content hashes for surviving documents ---
    from app.api.ingest import compute_content_hash

    for doc_id_prefix, path in SURVIVORS:
        doc = db.query(Document).filter(Document.doc_id == doc_id_prefix).first()
        if doc is None:
            print(f"[Dedupe] WARNING: no document matching {doc_id_prefix} — skipped")
            continue
        if doc.content_hash:
            print(f"[Dedupe] {doc.title!r} already has content_hash — skipped")
            continue
        raw_doc = load_document(path)
        doc.content_hash = compute_content_hash(raw_doc.text)
        print(f"[Dedupe] Backfilled content_hash for {doc.title!r} ({doc.doc_id})")

    db.commit()
    db.close()

    # --- 3. Report final state ---
    db = SessionLocal()
    docs = db.query(Document).all()
    n_chunks = db.query(Chunk).count()
    print(f"[Dedupe] Final state: {len(docs)} documents, {n_chunks} chunks")
    for d in docs:
        print(f"  - {d.doc_id} | {d.title!r} | hash={'yes' if d.content_hash else 'NO'}")
    db.close()


if __name__ == "__main__":
    main()
