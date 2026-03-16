from pydantic import BaseModel, Field
import uuid


class Chunk(BaseModel):
    chunk_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    topic: str
    source_file: str
    chunk_index: int
    char_count: int
    embedding: list[float] | None = None
