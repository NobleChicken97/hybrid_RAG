"""
Configuration module for the Hybrid RAG System.

Loads settings from environment variables / .env file.
All paths are relative to the project root and resolved at startup.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

# Project root = parent of the 'app/' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- LLM Backends ---
    environment: str = Field(default="local", description="Environment: 'local' or 'production'")
    llm_backend: str = Field(default="ollama_qwen3", description="Primary LLM backend to use")
    ragas_judge_backend: str = Field(default="cerebras", description="LLM backend to use for RAGAS eval judge")

    # API Keys & Hosts
    ollama_host: str = Field(default="http://localhost:11434", description="Ollama API base URL")
    ollama_model_primary: str = Field(default="qwen3:4b", description="Primary local Ollama model")
    ollama_model_secondary: str = Field(default="phi4-mini", description="Secondary local Ollama model")

    cerebras_api_key: str = Field(default="", description="Cerebras API key")
    cerebras_model: str = Field(default="llama3.3-70b", description="Cerebras model")
    cerebras_base_url: str = Field(default="https://api.cerebras.ai/v1", description="Cerebras base URL")

    gemini_api_key: str = Field(default="", description="Google Gemini API key")
    gemini_model: str = Field(default="gemini-3.7-flash", description="Gemini model for generation")
    gemini_base_url: str = Field(
        default="https://generativelanguage.googleapis.com/v1beta/openai/",
        description="Gemini OpenAI-compatible base URL",
    )

    groq_api_key: str = Field(default="", description="Groq API key")
    groq_model: str = Field(default="llama-3.3-70b-versatile", description="Groq model")
    groq_base_url: str = Field(default="https://api.groq.com/openai/v1", description="Groq base URL")

    ragas_judge_model: str = Field(default="llama-3.3-70b-versatile", description="RAGAS Judge model name")

    anthropic_api_key: str = Field(default="", description="Anthropic API key for Claude")

    # --- Embedding Model ---
    embedding_model: str = Field(
        default="BAAI/bge-small-en-v1.5",
        description="HuggingFace model ID for chunk/query embeddings",
    )
    embedding_dimension: int = Field(default=384, description="Embedding vector dimension for BGE-small")

    # --- Reranker Model ---
    reranker_model: str = Field(
        default="cross-encoder/ms-marco-MiniLM-L-6-v2",
        description="HuggingFace model ID for cross-encoder reranking",
    )

    # --- Retrieval ---
    retrieval_top_k: int = Field(default=20, description="Top-K candidates from each retrieval method")
    rerank_top_n: int = Field(default=5, description="Top-N results after cross-encoder reranking")
    rrf_k: int = Field(default=60, description="RRF constant k (standard = 60)")

    # --- Paths (relative to project root) ---
    chroma_db_path: str = Field(default="data/chroma_db")
    bm25_index_path: str = Field(default="data/bm25_index")
    sqlite_db_path: str = Field(default="data/hybrid_rag.db")
    qa_sets_path: str = Field(default="data/qa_sets")
    sample_docs_path: str = Field(default="sample_docs")
    upload_dir: str = Field(default="data/uploads")

    # --- Server ---
    backend_host: str = Field(default="0.0.0.0")
    backend_port: int = Field(default=8000)

    # --- Context Compression ---
    compression_threshold: float = Field(
        default=0.3,
        description="Minimum cross-encoder score for a sentence to be kept during compression",
    )
    max_context_tokens: int = Field(
        default=2000,
        description="Maximum total tokens in the compressed context sent to the LLM",
    )

    model_config = {
        "env_file": str(PROJECT_ROOT / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    # --- Resolved Paths ---
    @property
    def chroma_db_abs_path(self) -> Path:
        return PROJECT_ROOT / self.chroma_db_path

    @property
    def bm25_index_abs_path(self) -> Path:
        return PROJECT_ROOT / self.bm25_index_path

    @property
    def sqlite_db_abs_path(self) -> Path:
        return PROJECT_ROOT / self.sqlite_db_path

    @property
    def qa_sets_abs_path(self) -> Path:
        return PROJECT_ROOT / self.qa_sets_path

    @property
    def sample_docs_abs_path(self) -> Path:
        return PROJECT_ROOT / self.sample_docs_path

    @property
    def upload_abs_path(self) -> Path:
        return PROJECT_ROOT / self.upload_dir

    @property
    def sqlite_url(self) -> str:
        return f"sqlite+aiosqlite:///{self.sqlite_db_abs_path}"


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings (singleton)."""
    return Settings()
