"""
ChromaDB persistent vector store wrapper.

Provides add_chunks() and query() methods used by the RetrieverAgent.
Uses a singleton pattern so the collection is shared across requests.
"""

from __future__ import annotations

import logging
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from backend.config import settings

logger = logging.getLogger(__name__)

_client: chromadb.ClientAPI | None = None
_collection: chromadb.Collection | None = None


def _get_collection() -> chromadb.Collection:
    """Lazily initialise the ChromaDB client and collection."""
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        _collection = _client.get_or_create_collection(
            name=settings.chroma_collection,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "ChromaDB collection '%s' loaded — %d documents",
            settings.chroma_collection,
            _collection.count(),
        )
    return _collection


def add_chunks(
    chunks: list[dict[str, Any]],
    embeddings: list[list[float]],
) -> None:
    """
    Persist text chunks and their embeddings into ChromaDB.

    Args:
        chunks: List of dicts with keys ``text`` and ``metadata``.
        embeddings: Pre-computed embeddings aligned with ``chunks``.
    """
    collection = _get_collection()
    existing_count = collection.count()

    ids = [str(existing_count + i) for i in range(len(chunks))]
    documents = [c["text"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    logger.info("Added %d chunks to ChromaDB (total: %d)", len(chunks), collection.count())


def query_chunks(
    query_embedding: list[float],
    top_k: int = 10,
) -> list[dict[str, Any]]:
    """
    Retrieve the top-K most similar chunks via cosine similarity.

    Returns a list of dicts with keys: ``text``, ``metadata``, ``score``.
    """
    collection = _get_collection()
    if collection.count() == 0:
        logger.warning("ChromaDB collection is empty — no results.")
        return []

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append(
            {
                "text": doc,
                "metadata": meta,
                "score": float(1 - dist),  # cosine distance → similarity
            }
        )
    return chunks


def get_collection_count() -> int:
    """Return total number of stored chunks."""
    return _get_collection().count()


def reset_collection() -> None:
    """Drop and recreate the collection (useful for testing)."""
    global _collection
    if _client is not None:
        _client.delete_collection(settings.chroma_collection)
        _collection = None
        _get_collection()
        logger.info("Collection reset.")
