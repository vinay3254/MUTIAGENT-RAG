"""
FastAPI route definitions.

Endpoints:
  GET  /health       — liveness check
  POST /ingest       — upload a document (PDF / TXT / MD)
  POST /query        — run the full RAG pipeline and return a structured answer
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from backend.agents.orchestrator import run_pipeline
from backend.agents.retriever import RetrieverAgent
from backend.ingestion.loader import ingest_upload, SUPPORTED_EXTENSIONS
from backend.vector_store.chroma_store import add_chunks, get_collection_count

logger = logging.getLogger(__name__)
router = APIRouter()

_retriever = RetrieverAgent()


# --------------------------------------------------------------------------- #
# Request / Response models                                                     #
# --------------------------------------------------------------------------- #

class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    query: str
    answer: str
    citations: list[dict[str, Any]]
    fact_check: dict[str, Any]
    pipeline_log: list[str]
    retry_count: int


class IngestResponse(BaseModel):
    filename: str
    chunks_added: int
    total_chunks: int


class HealthResponse(BaseModel):
    status: str
    total_chunks: int


# --------------------------------------------------------------------------- #
# Routes                                                                        #
# --------------------------------------------------------------------------- #

@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Liveness check — also reports total chunks stored."""
    return HealthResponse(status="ok", total_chunks=get_collection_count())


@router.post("/ingest", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...)) -> IngestResponse:
    """
    Upload a document and store its chunks in ChromaDB.

    Accepts: PDF, TXT, MD.
    """
    filename = file.filename or "unknown"
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type '{ext}'. Allowed: {sorted(SUPPORTED_EXTENSIONS)}",
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=422, detail="Uploaded file is empty.")

    logger.info("[/ingest] Processing '%s' (%d bytes)", filename, len(file_bytes))

    try:
        chunks = await ingest_upload(file_bytes, filename)
    except Exception as exc:
        logger.error("[/ingest] Ingestion failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

    # Embed all chunks
    embeddings = [_retriever.encode(c["text"]) for c in chunks]
    add_chunks(chunks, embeddings)

    total = get_collection_count()
    logger.info("[/ingest] '%s' → %d chunks added (total: %d)", filename, len(chunks), total)

    return IngestResponse(
        filename=filename,
        chunks_added=len(chunks),
        total_chunks=total,
    )


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest) -> QueryResponse:
    """
    Run the full Multi-Agent RAG pipeline for a user question.

    Pipeline: Retriever → Ranker → Synthesizer → FactChecker (with re-retrieval loop).
    """
    if not request.query.strip():
        raise HTTPException(status_code=422, detail="Query cannot be empty.")

    logger.info("[/query] Received query: %s", request.query)

    try:
        state = run_pipeline(request.query)
    except Exception as exc:
        logger.error("[/query] Pipeline failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

    synthesis = state.get("synthesis", {})
    fact_check = state.get("fact_check", {})

    return QueryResponse(
        query=request.query,
        answer=synthesis.get("answer", "No answer generated."),
        citations=synthesis.get("citations", []),
        fact_check=fact_check,
        pipeline_log=state.get("pipeline_log", []),
        retry_count=state.get("retry_count", 0),
    )
