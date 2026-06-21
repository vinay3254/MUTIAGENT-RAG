"""
Document ingestion pipeline.

Supports PDF, plain text (.txt), and Markdown (.md) files.
Splits documents into overlapping chunks using LangChain's
RecursiveCharacterTextSplitter, then returns structured chunk dicts.
"""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import Any

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.config import settings

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}


def _get_loader(file_path: str):
    """Return the appropriate LangChain loader based on file extension."""
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return PyPDFLoader(file_path)
    elif ext in {".txt", ".md"}:
        return TextLoader(file_path, encoding="utf-8")
    else:
        raise ValueError(
            f"Unsupported file type '{ext}'. Supported: {SUPPORTED_EXTENSIONS}"
        )


def load_and_chunk(file_path: str) -> list[dict[str, Any]]:
    """
    Load a document from ``file_path`` and split it into chunks.

    Returns:
        List of dicts with keys ``text`` and ``metadata``
        (``source``, ``page`` where available).
    """
    loader = _get_loader(file_path)
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    split_docs = splitter.split_documents(documents)

    chunks: list[dict[str, Any]] = []
    source_name = Path(file_path).name

    for doc in split_docs:
        meta = dict(doc.metadata)
        meta.setdefault("source", source_name)
        # PyPDFLoader stores page number as 'page' (0-indexed) — normalise to 1-indexed
        if "page" in meta:
            meta["page"] = int(meta["page"]) + 1
        chunks.append({"text": doc.page_content, "metadata": meta})

    logger.info(
        "Loaded '%s' → %d chunks (chunk_size=%d, overlap=%d)",
        source_name,
        len(chunks),
        settings.chunk_size,
        settings.chunk_overlap,
    )
    return chunks


async def ingest_upload(
    file_bytes: bytes,
    filename: str,
) -> list[dict[str, Any]]:
    """
    Accept raw file bytes (from FastAPI UploadFile), save to a temp file,
    run chunking, return chunks.
    """
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        return load_and_chunk(tmp_path)
    finally:
        os.unlink(tmp_path)
