"""
POST /ingest — Document ingestion endpoint.

Pipeline: upload/raw_text → load → chunk → embed → store (ChromaDB + BM25 + SQLite)
"""

import hashlib
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import Chunk, Document, get_db
from app.ingestion.chunker import chunk_document
from app.ingestion.embedder import embed_chunks
from app.ingestion.loader import load_document, load_from_raw_text
from app.models import ChunkPreview, IngestResponse
from app.retrieval import bm25_index, vector_store

router = APIRouter(tags=["Ingestion"])


def compute_content_hash(text: str) -> str:
    """SHA-256 of the document text — the duplicate-ingestion fingerprint."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    file: UploadFile | None = File(None),
    title: str = Form("Untitled"),
    raw_text: str | None = Form(None),
    db: Session = Depends(get_db),
):
    """
    Ingest a document into the RAG system.

    Accepts either a file upload (PDF/MD/TXT) or raw text.
    The document is chunked, embedded, and indexed in both
    the vector store and BM25 index.
    """
    settings = get_settings()

    # --- Validate input ---
    if file is None and raw_text is None:
        raise HTTPException(
            status_code=400,
            detail="Provide either a file upload or raw_text.",
        )

    # --- Generate document ID ---
    doc_id = f"doc_{uuid.uuid4().hex[:12]}"

    # --- Load document ---
    uploaded_path: Path | None = None
    if file is not None:
        # Save uploaded file to disk
        upload_dir = settings.upload_abs_path
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / f"{doc_id}_{file.filename}"
        uploaded_path = file_path

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        try:
            raw_doc = load_document(file_path)
            raw_doc.title = title
        except ValueError as e:
            # Clean up the uploaded file
            file_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail=str(e)) from e
    else:
        raw_doc = load_from_raw_text(raw_text, title)

    # --- Duplicate guard ---
    # The same content ingested twice would be indexed twice, wasting
    # retrieval slots and producing duplicate citations (observed: a PDF
    # uploaded twice ended up double-indexed).
    content_hash = compute_content_hash(raw_doc.text)
    existing = db.query(Document).filter(Document.content_hash == content_hash).first()
    if existing is not None:
        if uploaded_path is not None:
            uploaded_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=409,
            detail=(
                f"This document was already ingested as '{existing.title}' "
                f"(doc_id={existing.doc_id}). Ingesting it again would duplicate "
                f"its chunks in the index."
            ),
        )

    # --- Chunk ---
    chunks = chunk_document(raw_doc, doc_id)

    if not chunks:
        raise HTTPException(
            status_code=400,
            detail="Document produced zero chunks. It may be empty or too short.",
        )

    # --- Embed ---
    chunk_texts = [c.text for c in chunks]
    chunk_ids = [c.chunk_id for c in chunks]
    embeddings = embed_chunks(chunk_texts)

    # --- Store in vector store (ChromaDB) ---
    metadatas = [
        {
            "doc_id": c.doc_id,
            "doc_title": title,
            "section_header": c.section_header or "",
            "token_count": c.token_count,
            "source_path": raw_doc.source_path,
        }
        for c in chunks
    ]
    vector_store.add_chunks(chunk_ids, embeddings, chunk_texts, metadatas)

    # --- Store in BM25 index ---
    bm25_index.add_to_index(chunk_ids, chunk_texts)

    # --- Store metadata in SQLite ---
    db_doc = Document(
        doc_id=doc_id,
        source_path=raw_doc.source_path,
        title=title,
        content_hash=content_hash,
    )
    db.add(db_doc)

    for chunk in chunks:
        db_chunk = Chunk(
            chunk_id=chunk.chunk_id,
            doc_id=doc_id,
            text=chunk.text,
            start_offset=chunk.start_offset,
            end_offset=chunk.end_offset,
            token_count=chunk.token_count,
            section_header=chunk.section_header,
        )
        db.add(db_chunk)

    db.commit()

    # --- Build response ---
    sample_chunks = [
        ChunkPreview(
            chunk_id=c.chunk_id,
            text_preview=c.text[:200],
            token_count=c.token_count,
            section_header=c.section_header,
        )
        for c in chunks[:5]  # Show first 5 chunks as preview
    ]

    return IngestResponse(
        doc_id=doc_id,
        title=title,
        chunk_count=len(chunks),
        sample_chunks=sample_chunks,
    )
