"""
Central configuration — loads from .env file via Pydantic BaseSettings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Anthropic
    anthropic_api_key: str = ""

    # Models
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    llm_model: str = "claude-sonnet-4-6"

    # Retrieval
    top_k: int = 10          # chunks returned by retriever
    top_n: int = 3           # chunks kept after reranking
    confidence_threshold: float = 0.6   # fact-checker threshold for re-retrieval

    # ChromaDB
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection: str = "rag_documents"

    # Chunking
    chunk_size: int = 500
    chunk_overlap: int = 50

    # Orchestrator
    max_retries: int = 2


settings = Settings()
