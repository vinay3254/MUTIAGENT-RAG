"""
FastAPI application entrypoint.

Run with:
    uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)

app = FastAPI(
    title="Multi-Agent RAG API",
    description=(
        "A five-agent RAG pipeline: Retriever → Ranker → Synthesizer → FactChecker, "
        "orchestrated by LangGraph with automatic re-retrieval loops."
    ),
    version="1.0.0",
)

# Allow the React dev server (port 5173) and any deployed frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="")


@app.on_event("startup")
async def startup_event() -> None:
    logging.getLogger(__name__).info(
        "Multi-Agent RAG API starting up. "
        "Chroma dir: %s | LLM: %s",
        settings.chroma_persist_dir,
        settings.llm_model,
    )
