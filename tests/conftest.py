"""Session-wide test isolation.

Sets all data-path settings to a throwaway directory BEFORE any app module is
imported, so tests never touch the real data/ stores and the API smoke test
can boot the app against a clean, isolated environment.

Settings are lru_cached at first use, so these env vars must be in place
before the first get_settings() call anywhere in the process.
"""

import tempfile
from pathlib import Path

_TMP_DATA = Path(tempfile.mkdtemp(prefix="hybrid_rag_test_"))

import os

os.environ.setdefault("CHROMA_DB_PATH", str(_TMP_DATA / "chroma_db"))
os.environ.setdefault("BM25_INDEX_PATH", str(_TMP_DATA / "bm25_index"))
os.environ.setdefault("SQLITE_DB_PATH", str(_TMP_DATA / "test.db"))
os.environ.setdefault("UPLOAD_DIR", str(_TMP_DATA / "uploads"))
# CI has no API keys; make sure no test can accidentally hit a cloud backend.
os.environ.setdefault("LLM_BACKEND", "ollama_qwen3")
os.environ.setdefault("ENVIRONMENT", "local")
