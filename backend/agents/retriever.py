"""
RetrieverAgent

Embeds the user query using sentence-transformers/all-MiniLM-L6-v2,
then performs a cosine-similarity search against the ChromaDB collection
and returns the top-K most relevant chunks.
"""

from __future__ import annotations

import logging
from typing import Any

from sentence_transformers import SentenceTransformer

from backend.config import settings
from backend.vector_store.chroma_store import query_chunks

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Singleton — model is loaded once at import time to avoid cold-start latency #
# --------------------------------------------------------------------------- #
_encoder: SentenceTransformer | None = None


def _get_encoder() -> SentenceTransformer:
    global _encoder
    if _encoder is None:
        logger.info("Loading embedding model: %s", settings.embedding_model)
        _encoder = SentenceTransformer(settings.embedding_model)
    return _encoder


class RetrieverAgent:
    """
    Responsibilities:
    1. Encode the query into a dense vector.
    2. Query ChromaDB for the top-K nearest chunks.
    3. Return chunks with their similarity scores.
    """

    def encode(self, text: str) -> list[float]:
        """Return the embedding vector for a single text string."""
        encoder = _get_encoder()
        vector = encoder.encode(text, normalize_embeddings=True)
        return vector.tolist()

    def run(
        self,
        query: str,
        top_k: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Embed ``query`` and retrieve the top-K chunks from ChromaDB.

        Args:
            query: The user's natural-language question.
            top_k: Override the default ``settings.top_k``.

        Returns:
            List of chunk dicts: ``{text, metadata, score}``.
        """
        k = top_k or settings.top_k
        logger.info("[Retriever] Querying ChromaDB for top-%d chunks", k)

        embedding = self.encode(query)
        chunks = query_chunks(embedding, top_k=k)

        logger.info("[Retriever] Retrieved %d chunks", len(chunks))
        return chunks
