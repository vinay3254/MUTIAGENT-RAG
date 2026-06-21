"""
OrchestratorAgent — the Brain

Wires all four sub-agents into a LangGraph StateGraph:

    retrieve → rank → synthesize → fact_check
                ↑                       |
                └─── (retry loop) ──────┘
                     if confidence < threshold & retries < max

State flows through a TypedDict and each node mutates a slice of it.
"""

from __future__ import annotations

import logging
from typing import Any, Literal

from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from backend.agents.fact_checker import FactCheckerAgent
from backend.agents.ranker import RankerAgent
from backend.agents.retriever import RetrieverAgent
from backend.agents.synthesizer import SynthesizerAgent
from backend.config import settings

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Typed pipeline state                                                          #
# --------------------------------------------------------------------------- #

class AgentState(TypedDict):
    query: str
    refined_query: str           # may be same as query; modified on retry
    retry_count: int
    chunks: list[dict[str, Any]]
    ranked_chunks: list[dict[str, Any]]
    synthesis: dict[str, Any]
    fact_check: dict[str, Any]
    pipeline_log: list[str]      # human-readable step log for the frontend


# --------------------------------------------------------------------------- #
# Node functions                                                                #
# --------------------------------------------------------------------------- #

_retriever = RetrieverAgent()
_ranker = RankerAgent()
_synthesizer: SynthesizerAgent | None = None
_fact_checker: FactCheckerAgent | None = None


def _get_synthesizer() -> SynthesizerAgent:
    global _synthesizer
    if _synthesizer is None:
        _synthesizer = SynthesizerAgent()
    return _synthesizer


def _get_fact_checker() -> FactCheckerAgent:
    global _fact_checker
    if _fact_checker is None:
        _fact_checker = FactCheckerAgent()
    return _fact_checker


def retrieve_node(state: AgentState) -> AgentState:
    query = state.get("refined_query") or state["query"]
    logger.info("[Orchestrator] RETRIEVE — query: %s", query)
    chunks = _retriever.run(query)
    state["chunks"] = chunks
    state["pipeline_log"].append(
        f"Retriever: fetched {len(chunks)} chunks for query '{query}'"
    )
    return state


def rank_node(state: AgentState) -> AgentState:
    logger.info("[Orchestrator] RANK")
    query = state.get("refined_query") or state["query"]
    ranked = _ranker.run(query, state["chunks"])
    state["ranked_chunks"] = ranked
    state["pipeline_log"].append(
        f"Ranker: kept top-{len(ranked)} chunks after reranking"
    )
    return state


def synthesize_node(state: AgentState) -> AgentState:
    logger.info("[Orchestrator] SYNTHESIZE")
    result = _get_synthesizer().run(
        state["query"],
        state["ranked_chunks"],
    )
    state["synthesis"] = result
    state["pipeline_log"].append(
        f"Synthesizer: generated answer ({len(result['answer'])} chars)"
    )
    return state


def fact_check_node(state: AgentState) -> AgentState:
    logger.info("[Orchestrator] FACT-CHECK")
    result = _get_fact_checker().run(
        state["synthesis"]["answer"],
        state["ranked_chunks"],
    )
    state["fact_check"] = result
    state["pipeline_log"].append(
        f"FactChecker: confidence={result['overall_confidence']:.2f}  "
        f"reliable={result['is_reliable']}  "
        f"flagged={len(result.get('flagged_claims', []))}"
    )
    return state


# --------------------------------------------------------------------------- #
# Conditional routing after fact-check                                          #
# --------------------------------------------------------------------------- #

def should_retry(state: AgentState) -> Literal["retrieve", END]:  # type: ignore[valid-type]
    fc = state.get("fact_check", {})
    retry_count = state.get("retry_count", 0)

    if not fc.get("is_reliable", True) and retry_count < settings.max_retries:
        state["retry_count"] = retry_count + 1
        # Refine query by appending flagged claims as context hint
        flagged = fc.get("flagged_claims", [])
        if flagged:
            hint = " ".join(flagged[:2])  # use first two flagged claims
            state["refined_query"] = f"{state['query']} {hint}"
        else:
            state["refined_query"] = state["query"]

        logger.info(
            "[Orchestrator] Low confidence (%.2f) — retry %d/%d",
            fc.get("overall_confidence", 0),
            state["retry_count"],
            settings.max_retries,
        )
        state["pipeline_log"].append(
            f"Orchestrator: re-retrieval triggered (retry {state['retry_count']}/{settings.max_retries})"
        )
        return "retrieve"

    return END


# --------------------------------------------------------------------------- #
# Graph assembly                                                                #
# --------------------------------------------------------------------------- #

def _build_graph() -> Any:
    graph = StateGraph(AgentState)

    graph.add_node("retrieve", retrieve_node)
    graph.add_node("rank", rank_node)
    graph.add_node("synthesize", synthesize_node)
    graph.add_node("fact_check", fact_check_node)

    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "rank")
    graph.add_edge("rank", "synthesize")
    graph.add_edge("synthesize", "fact_check")
    graph.add_conditional_edges(
        "fact_check",
        should_retry,
        {"retrieve": "retrieve", END: END},
    )

    return graph.compile()


_pipeline = _build_graph()


# --------------------------------------------------------------------------- #
# Public API                                                                    #
# --------------------------------------------------------------------------- #

def run_pipeline(query: str) -> dict[str, Any]:
    """
    Execute the full RAG pipeline for a user query.

    Returns the final ``AgentState`` as a plain dict.
    """
    logger.info("[Orchestrator] Pipeline START — query: %s", query)

    initial_state: AgentState = {
        "query": query,
        "refined_query": query,
        "retry_count": 0,
        "chunks": [],
        "ranked_chunks": [],
        "synthesis": {},
        "fact_check": {},
        "pipeline_log": [],
    }

    final_state = _pipeline.invoke(initial_state)
    logger.info("[Orchestrator] Pipeline END")
    return final_state
