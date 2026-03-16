from sentence_transformers import SentenceTransformer
from educateai.core.models import Chunk


_model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2")  # load once


def embed_chunks(chunks: list[Chunk]) -> list[Chunk]:
    """
    Placeholder function for embedding chunks of text.

    Args:
        chunks (List[Chunk]): A list of Chunk objects to be embedded.

    Returns:
        None
    """
    for chunk in chunks:
        chunk.embedding = _model.encode(chunk.text).tolist()
        print(chunk.embedding)  # For demonstration, print the embedding vector
    return chunks