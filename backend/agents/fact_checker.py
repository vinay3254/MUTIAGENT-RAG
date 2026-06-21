"""
FactCheckerAgent

Verifies that every sentence in the synthesized answer is grounded in
the retrieved chunks. Uses Claude to perform sentence-level entailment
checking. Returns a confidence score and a list of flagged claims.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import anthropic

from backend.config import settings

logger = logging.getLogger(__name__)

FACT_CHECK_SYSTEM_PROMPT = """You are a rigorous fact-checking assistant.

You will be given:
1. A list of source context chunks (the ground truth).
2. An answer that was generated from those chunks.

Your task:
- Split the answer into individual factual sentences.
- For each sentence, determine if it is SUPPORTED or UNSUPPORTED by the context chunks.
- Ignore filler sentences, transitions, or hedging phrases (e.g., "Based on the context...").

Respond ONLY with valid JSON in this exact schema (no markdown, no explanation):
{
  "sentences": [
    {
      "text": "<the sentence>",
      "supported": true | false,
      "supporting_source": "<source filename or null>",
      "confidence": <0.0 to 1.0>
    }
  ],
  "overall_confidence": <0.0 to 1.0>,
  "flagged_claims": ["<unsupported sentence 1>", ...]
}
"""


class FactCheckerAgent:
    """
    Responsibilities:
    1. Tokenize the answer into sentences.
    2. Ask Claude to verify each sentence against the context chunks.
    3. Return a structured verification report with confidence score.
    """

    def __init__(self) -> None:
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def run(
        self,
        answer: str,
        chunks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Verify the answer against the retrieved chunks.

        Returns:
            ``{overall_confidence, sentences, flagged_claims, is_reliable}``
        """
        if not answer or not chunks:
            return {
                "overall_confidence": 0.0,
                "sentences": [],
                "flagged_claims": [],
                "is_reliable": False,
            }

        context_text = "\n\n".join(
            f"[{c['metadata'].get('source', 'unknown')}] {c['text']}" for c in chunks
        )

        user_message = f"""CONTEXT CHUNKS:
{context_text}

---

ANSWER TO VERIFY:
{answer}

Verify each factual sentence in the answer against the context chunks. Return JSON only."""

        logger.info("[FactChecker] Sending answer for verification")

        try:
            response = self._client.messages.create(
                model=settings.llm_model,
                max_tokens=1024,
                system=FACT_CHECK_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            )

            raw = response.content[0].text.strip()

            # Strip markdown code fences if Claude wraps the JSON
            raw = re.sub(r"^```(?:json)?\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)

            result: dict = json.loads(raw)

        except (json.JSONDecodeError, Exception) as exc:
            logger.error("[FactChecker] Failed to parse response: %s", exc)
            # Fallback — treat as unverified
            result = {
                "sentences": [],
                "overall_confidence": 0.5,
                "flagged_claims": [],
            }

        confidence = float(result.get("overall_confidence", 0.5))
        result["is_reliable"] = confidence >= settings.confidence_threshold

        logger.info(
            "[FactChecker] confidence=%.2f  reliable=%s  flagged=%d",
            confidence,
            result["is_reliable"],
            len(result.get("flagged_claims", [])),
        )
        return result
