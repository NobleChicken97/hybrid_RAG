"""
Tests for the ingestion duplicate guard (2026-09-02 fix).

The same document ingested twice used to be indexed twice (observed with a
PDF uploaded two times), wasting retrieval slots and producing duplicate
citations. These tests cover the fingerprint and the duplicate-lookup query
used by POST /ingest.
"""


from sqlalchemy.orm import sessionmaker

from app.api.ingest import compute_content_hash
from app.database import Base, Document


class TestContentHash:
    def test_deterministic(self):
        assert compute_content_hash("some document text") == compute_content_hash(
            "some document text"
        )

    def test_differs_for_different_text(self):
        assert compute_content_hash("text a") != compute_content_hash("text b")

    def test_differs_for_whitespace_only_change(self):
        # Whitespace changes alter the extracted text, so they are a
        # different fingerprint — strictness is intentional.
        assert compute_content_hash("text a") != compute_content_hash("text a ")

    def test_is_sha256_hex(self):
        h = compute_content_hash("x")
        assert len(h) == 64
        int(h, 16)  # parses as hex


class TestDuplicateLookup:
    def _make_session(self, tmp_path):
        engine = __import__("sqlalchemy").create_engine(
            f"sqlite:///{tmp_path / 'test.db'}",
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(bind=engine)
        return sessionmaker(bind=engine)()

    def test_existing_hash_found(self, tmp_path):
        db = self._make_session(tmp_path)
        h = compute_content_hash("gatsby text")
        db.add(Document(doc_id="doc_1", title="Gatsby", content_hash=h))
        db.commit()

        existing = db.query(Document).filter(Document.content_hash == h).first()
        assert existing is not None
        assert existing.title == "Gatsby"

    def test_unknown_hash_misses(self, tmp_path):
        db = self._make_session(tmp_path)
        db.add(Document(doc_id="doc_1", title="Other", content_hash="a" * 64))
        db.commit()

        missing = db.query(Document).filter(Document.content_hash == "b" * 64).first()
        assert missing is None

    def test_nullable_hash_columns_do_not_collide(self, tmp_path):
        # Legacy rows (pre-migration) have NULL content_hash; NULL must not
        # match anything in the duplicate lookup.
        db = self._make_session(tmp_path)
        db.add(Document(doc_id="doc_legacy", title="Legacy", content_hash=None))
        db.commit()


        result = (
            db.query(Document).filter(Document.content_hash == compute_content_hash("x")).first()
        )
        assert result is None
        assert db.query(Document).count() == 1
