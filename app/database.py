"""
SQLAlchemy database models and session management for the Hybrid RAG System.

Tables:
  - documents: Ingested document metadata
  - chunks: Text chunks with offsets and token counts
  - qa_eval_items: Held-out QA pairs for evaluation
  - eval_runs: Evaluation run results and scorecards
"""

import json
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""
    pass


class Document(Base):
    """An ingested source document."""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(String(64), unique=True, nullable=False, index=True)
    source_path = Column(String(512), nullable=True)
    title = Column(String(256), nullable=False)
    # SHA-256 of the document text; used to reject duplicate ingestion
    # (a PDF uploaded twice used to be indexed twice, wasting retrieval slots).
    content_hash = Column(String(64), nullable=True, index=True)
    ingested_at = Column(DateTime, default=lambda: datetime.now(UTC))

    # Relationship to chunks
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Document(doc_id={self.doc_id!r}, title={self.title!r})>"


class Chunk(Base):
    """A text chunk from a document."""
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chunk_id = Column(String(128), unique=True, nullable=False, index=True)
    doc_id = Column(String(64), ForeignKey("documents.doc_id"), nullable=False, index=True)
    text = Column(Text, nullable=False)
    start_offset = Column(Integer, nullable=True)
    end_offset = Column(Integer, nullable=True)
    token_count = Column(Integer, nullable=True)
    section_header = Column(String(512), nullable=True)  # For context tracking

    # Relationship back to document
    document = relationship("Document", back_populates="chunks")

    def __repr__(self) -> str:
        return f"<Chunk(chunk_id={self.chunk_id!r}, doc_id={self.doc_id!r}, tokens={self.token_count})>"


class QAEvalItem(Base):
    """A held-out question/answer pair for evaluation."""
    __tablename__ = "qa_eval_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    qa_id = Column(String(64), unique=True, nullable=False, index=True)
    qa_set_name = Column(String(128), nullable=False, default="default")
    question = Column(Text, nullable=False)
    ground_truth_answer = Column(Text, nullable=False)
    ground_truth_chunk_ids = Column(Text, nullable=False)  # JSON array of chunk IDs

    def get_chunk_ids(self) -> list[str]:
        """Parse the JSON chunk IDs."""
        return json.loads(self.ground_truth_chunk_ids)

    def __repr__(self) -> str:
        return f"<QAEvalItem(qa_id={self.qa_id!r}, question={self.question[:50]!r}...)>"


class EvalRun(Base):
    """A single evaluation run with scores and configuration snapshot."""
    __tablename__ = "eval_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(64), unique=True, nullable=False, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC))
    retrieval_mode = Column(String(32), nullable=False, default="hybrid")  # 'vector_only' | 'hybrid'
    config_snapshot = Column(Text, nullable=True)  # JSON of pipeline config at time of run

    # Aggregate scores
    faithfulness = Column(Float, nullable=True)
    answer_relevancy = Column(Float, nullable=True)
    context_precision = Column(Float, nullable=True)
    context_recall = Column(Float, nullable=True)

    # Detailed per-question breakdown (JSON)
    per_question_scores = Column(Text, nullable=True)

    def get_config(self) -> dict:
        """Parse config snapshot."""
        return json.loads(self.config_snapshot) if self.config_snapshot else {}

    def get_per_question(self) -> list[dict]:
        """Parse per-question scores."""
        return json.loads(self.per_question_scores) if self.per_question_scores else []

    def __repr__(self) -> str:
        return (
            f"<EvalRun(run_id={self.run_id!r}, mode={self.retrieval_mode!r}, "
            f"faithfulness={self.faithfulness})>"
        )


# ─── Engine & Session ────────────────────────────────────────────────────────

_engine = None
_SessionLocal = None


def get_engine():
    """Get or create the SQLAlchemy engine (singleton)."""
    global _engine
    if _engine is None:
        settings = get_settings()
        # Ensure the parent directory exists
        settings.sqlite_db_abs_path.parent.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(
            f"sqlite:///{settings.sqlite_db_abs_path}",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False,
        )
    return _engine


def get_session_factory():
    """Get or create the session factory (singleton)."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autocommit=False, autoflush=False)
    return _SessionLocal


def get_db() -> Session:
    """FastAPI dependency: yield a DB session, auto-close on exit."""
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables if they don't exist, then add missing columns.

    create_all() only creates new tables — it never alters existing ones —
    so pre-existing databases are upgraded with lightweight ALTER TABLEs
    (safe on SQLite) instead of requiring a wipe that would lose eval history.
    """
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    from sqlalchemy import text as sql_text
    with engine.connect() as conn:
        doc_cols = {row[1] for row in conn.execute(sql_text("PRAGMA table_info(documents)"))}
        if "content_hash" not in doc_cols:
            conn.execute(sql_text("ALTER TABLE documents ADD COLUMN content_hash VARCHAR(64)"))
            conn.commit()
            print("[DB] Migrated documents table: added content_hash column.")

    print("[DB] Tables created / verified.")
