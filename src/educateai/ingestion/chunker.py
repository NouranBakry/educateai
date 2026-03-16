import re

from educateai.core.models import Chunk


# ── Stage 1: Structural split ─────────────────────────────────────────────────

HEADER_PATTERN = re.compile(
    r"(?m)^(?:#{1,3}\s+.+|(?:\d+\.\s+)[A-Z].+|\*\*[A-Z][^*]+\*\*)$"
)


def structural_split(text: str) -> list[str]:
    """
    Splits the text into chunks based on structural elements like headers.
    Each segment is prefixed with its header so the topic can be derived later.
    """
    parts = HEADER_PATTERN.split(text)
    headers = HEADER_PATTERN.findall(text)
    segments = []
    for i, part in enumerate(parts):
        header = headers[i - 1] if i > 0 else ""
        combined = (header + "\n" + part).strip()
        if combined:
            sub_parts = [s.strip() for s in combined.split("\n\n") if s.strip()]
            segments.extend(sub_parts)

    return segments or [text]


def merge_small_chunks(segments: list[str], min_chars: int = 150) -> list[str]:
    """
    Merges segments shorter than min_chars into the previous segment.
    Prevents tiny orphan chunks that are too short to embed meaningfully.
    """
    merged = []
    for seg in segments:
        if merged and len(seg) < min_chars:
            merged[-1] += "\n\n" + seg
        else:
            merged.append(seg)
    return merged


def split_large_chunks(segments: list[str], max_chars: int = 1200) -> list[str]:
    """
    Splits segments longer than max_chars at sentence boundaries.
    Never cuts mid-sentence.
    """
    result = []
    for seg in segments:
        if len(seg) <= max_chars:
            result.append(seg)
        else:
            sentences = re.split(r"(?<=[.!?])\s+", seg)
            current = ""
            for sentence in sentences:
                if len(current) + len(sentence) > max_chars and current:
                    result.append(current.strip())
                    current = sentence
                else:
                    current += " " + sentence
            if current.strip():
                result.append(current.strip())
    return result


# ── Stage 2: Topic extraction from headers ────────────────────────────────────

def _extract_topic(segment: str) -> str:
    """
    Derives a topic label from the segment itself — no API call needed.

    Priority:
    1. If the first line is a header (## Photosynthesis) → strip the # and use it
    2. Otherwise → use the first sentence, truncated to 60 chars
    """
    first_line = segment.split("\n")[0].strip()
    if first_line.startswith("#"):
        return re.sub(r"^#+\s*", "", first_line)[:60]
    first_sentence = segment.split(".")[0][:60].strip()
    return first_sentence or "Section"


# ── Public API ────────────────────────────────────────────────────────────────

def smart_chunker(text: str, source_file: str = "unknown") -> list[Chunk]:
    """
    Splits text into Chunk objects ready for embedding and storage.

    Pipeline:
        structural_split → merge_small_chunks → split_large_chunks → topic from header
    """
    segments = structural_split(text)
    segments = merge_small_chunks(segments, min_chars=150)
    segments = split_large_chunks(segments, max_chars=1200)

    return [
        Chunk(
            text=seg,
            topic=_extract_topic(seg),
            source_file=source_file,
            chunk_index=i,
            char_count=len(seg),
        )
        for i, seg in enumerate(segments)
    ]
