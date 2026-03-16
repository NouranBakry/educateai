"""Stores embedded chunks to ChromaDB and provides similarity search."""

from educateai.core.models import Chunk
import chromadb

_client = chromadb.PersistentClient(path="data/chromadb")
_collection = _client.get_or_create_collection(name="chunks")


def save_chunks(chunks: list[Chunk]) -> None:
    """
    Persists embedded chunks to ChromaDB in a single batched call.

    Args:
        chunks (list[Chunk]): Chunks with embedding field populated.

    Returns:
        None
    """
    _collection.add(
        ids=[chunk.chunk_id for chunk in chunks],
        documents=[chunk.text for chunk in chunks],
        embeddings=[chunk.embedding for chunk in chunks],
        metadatas=[{"topic": chunk.topic, "source_file": chunk.source_file, "chunk_index": chunk.chunk_index} for chunk in chunks]
    )

def search(query_embeddings: list[float], top_k: int = 5) -> list[dict]:
    """
    Search for relevant chunks based on query embeddings.

    Args:
        query_embeddings (list[float]): The embedding vector for the search query.
        top_k (int): The number of top results to return.

    Returns:
        list[dict]: A list of matching chunks with their metadata.
    """
    results = _collection.query(
        query_embeddings=[query_embeddings],
        n_results=top_k,
    )
    return results