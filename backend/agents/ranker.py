"""
RankerAgent

Uses a cross-encoder (ms-marco-MiniLM-L-6-v2) to re-score the top-K chunks
returned by the RetrieverAgent and keeps only the top-N highest-scoring ones.

Cross-encoders are slower than bi-encoders but significantly more accurate
because they process the (query, document) pair jointly.
"""

from __future__ import annotations

import logging
from typing import Any

from sentence_transformers import CrossEncoder

from backend.config import settings

logger = logging.getLogger(__name__)

_cross_encoder: CrossEncoder | None = None


def _get_cross_encoder() -> CrossEncoder:
    global _cross_encoder
    if _cross_encoder is None:
        logger.info("Loading reranker model: %s", settings.reranker_model)
        _cross_encoder = CrossEncoder(settings.reranker_model)
    return _cross_encoder


class RankerAgent:
    """
    Responsibilities:
    1. Score each (query, chunk) pair using the cross-encoder.
    2. Sort by descending score.
    3. Return the top-N chunks.
    """

    def run(
        self,
        query: str,
        chunks: list[dict[str, Any]],
        top_n: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Rerank ``chunks`` against ``query`` and return the top-N.

        Args:
            query:  The user's natural-language question.
            chunks: Chunks from the RetrieverAgent.
            top_n:  Override the default ``settings.top_n``.

        Returns:
            Reranked list of chunk dicts with an added ``rerank_score`` field.
        """
        n = top_n or settings.top_n

        if not chunks:
            logger.warning("[Ranker] No chunks to rerank.")
            return []

        cross_enc = _get_cross_encoder()
        pairs = [(query, chunk["text"]) for chunk in chunks]

        logger.info("[Ranker] Scoring %d (query, chunk) pairs", len(pairs))
        scores: list[float] = cross_enc.predict(pairs).tolist()

        # Attach scores and sort
        for chunk, score in zip(chunks, scores):
            chunk["rerank_score"] = score

        ranked = sorted(chunks, key=lambda c: c["rerank_score"], reverse=True)
        top = ranked[:n]

        logger.info(
            "[Ranker] Top-%d scores: %s",
            n,
            [round(c["rerank_score"], 4) for c in top],
        )
        return top
