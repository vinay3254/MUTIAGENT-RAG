"""
SynthesizerAgent

Calls claude-sonnet-4-6 via the Anthropic SDK.
Instructs the model to answer strictly from the provided context chunks
and to include inline citations in the format [Source: filename, p.N].
"""

from __future__ import annotations

import logging
from typing import Any

import anthropic

from backend.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a precise research assistant. Your ONLY job is to answer the user's question 
using the provided context chunks. 

STRICT RULES:
1. Answer ONLY from the information present in the provided context. Do NOT use prior knowledge.
2. Every factual claim MUST be followed by an inline citation in this exact format: [Source: <filename>, p.<page>]
   - Use the source filename and page number from the chunk metadata.
   - If page is unavailable, use [Source: <filename>].
3. If the context does not contain enough information to answer the question, explicitly state: 
   "The provided documents do not contain sufficient information to answer this question."
4. Do NOT fabricate facts, statistics, or details not present in the context.
5. Be concise, clear, and structured. Use bullet points or numbered lists where appropriate.
6. If multiple sources support a claim, cite all of them: [Source: a.pdf, p.2][Source: b.pdf, p.5]
"""


def _format_context(chunks: list[dict[str, Any]]) -> str:
    """Format chunks into a numbered context block for the prompt."""
    parts = []
    for i, chunk in enumerate(chunks, 1):
        meta = chunk.get("metadata", {})
        source = meta.get("source", "unknown")
        page = meta.get("page", "")
        page_str = f", p.{page}" if page else ""
        parts.append(f"[Chunk {i} | Source: {source}{page_str}]\n{chunk['text']}")
    return "\n\n---\n\n".join(parts)


class SynthesizerAgent:
    """
    Responsibilities:
    1. Format ranked chunks into a structured context block.
    2. Call Claude with a strict "answer only from context" system prompt.
    3. Return the answer text and extracted citation metadata.
    """

    def __init__(self) -> None:
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def run(
        self,
        query: str,
        chunks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Synthesize an answer from the ranked chunks.

        Returns:
            ``{answer: str, citations: list[dict], chunks_used: int}``
        """
        if not chunks:
            return {
                "answer": "No relevant documents were found to answer your question.",
                "citations": [],
                "chunks_used": 0,
            }

        context = _format_context(chunks)
        user_message = f"""CONTEXT:
{context}

---

QUESTION: {query}

Please answer the question using ONLY the context above, with inline citations."""

        logger.info("[Synthesizer] Calling %s for synthesis", settings.llm_model)

        response = self._client.messages.create(
            model=settings.llm_model,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )

        answer = response.content[0].text

        # Extract citation metadata from chunks used
        citations = []
        for chunk in chunks:
            meta = chunk.get("metadata", {})
            citations.append(
                {
                    "source": meta.get("source", "unknown"),
                    "page": meta.get("page"),
                    "text_preview": chunk["text"][:200] + "..."
                    if len(chunk["text"]) > 200
                    else chunk["text"],
                    "rerank_score": chunk.get("rerank_score"),
                }
            )

        logger.info("[Synthesizer] Answer generated (%d chars)", len(answer))
        return {
            "answer": answer,
            "citations": citations,
            "chunks_used": len(chunks),
        }
