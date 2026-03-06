"""
vector_store.py — ChromaDB Vector Store Integration
====================================================
WHY THIS FILE EXISTS:
When the Search Agent finds articles, we want to store them as vector
embeddings. This enables SEMANTIC search — finding related content based
on meaning, not just keywords.

Example: Searching for "machine learning fairness" would also find
documents about "algorithmic bias" and "AI discrimination" because
they're semantically similar, even though the exact words are different.

ChromaDB stores these embeddings LOCALLY (no cloud service needed).
It uses sentence-transformers to convert text into 384-dimensional vectors
and then uses approximate nearest neighbor search to find similar documents.

This is OPTIONAL — the system works without it, but with ChromaDB:
- The Analyzer gets richer context from semantic retrieval
- Previous research sessions can inform new ones
- We can find cross-topic connections
"""

import chromadb
from chromadb.config import Settings


# WHY persistent storage:
# By saving to disk (chroma_db/), embeddings survive app restarts.
# This means previous research articles are always available.
_client = None
_collection = None


def _get_collection():
    """
    Returns a singleton ChromaDB collection for research documents.

    WHY singleton:
    ChromaDB loads the index into memory. We don't want to reload it
    on every function call — that would be slow and wasteful.
    """
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path="./chroma_db")
        # WHY "research_documents":
        # A collection is like a table in a database. We use one collection
        # for all research documents across all sessions.
        _collection = _client.get_or_create_collection(
            name="research_documents",
            metadata={"description": "Stored research articles and sources"},
        )
    return _collection


def store_documents(documents, metadatas=None, ids=None):
    """
    Store documents as vector embeddings in ChromaDB.

    Args:
        documents: List of text strings to embed and store
        metadatas: Optional list of metadata dicts (e.g., {"source": "url", "title": "..."})
        ids: Optional list of unique IDs (auto-generated if not provided)

    WHY store metadata:
    When we retrieve similar documents later, we need to know WHERE they
    came from (URL) and WHAT they are (title). Metadata gives us this context.
    """
    collection = _get_collection()

    if ids is None:
        import uuid
        ids = [str(uuid.uuid4()) for _ in documents]

    if metadatas is None:
        metadatas = [{"source": "unknown"} for _ in documents]

    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids,
    )

    return ids


def query_similar(query_text, n_results=5):
    """
    Find documents semantically similar to the query.

    Args:
        query_text: The text to find similar documents for
        n_results: Number of results to return (default 5)

    Returns:
        Dict with 'documents', 'metadatas', and 'distances' keys

    WHY n_results=5:
    Enough to provide rich context without overwhelming the Analyzer.
    The most similar documents will have the smallest distances.
    """
    collection = _get_collection()

    results = collection.query(
        query_texts=[query_text],
        n_results=n_results,
    )

    return results
