from sentence_transformers import SentenceTransformer
from educateai.core.models import Chunk


_model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2")  # load once


def embed_chunks(chunks: list[Chunk]) -> list[Chunk]:
    """
    Encodes each chunk's text into a 384-dimensional vector using all-MiniLM-L6-v2.

    Args:
        chunks (list[Chunk]): Chunks to embed. Each chunk must have a non-empty text field.

    Returns:
        list[Chunk]: The same chunks with embedding field populated.
    """
    for chunk in chunks:
        chunk.embedding = _model.encode(chunk.text).tolist()
    return chunks