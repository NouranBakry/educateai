import re
import os
import json

import google.generativeai as genai

from educateai.core.models import Chunk


# ── Stage 1: Structural split ─────────────────────────────────────────────────

HEADER_PATTERN = re.compile(
    r"(?m)^(?:#{1,3}\s+.+|(?:\d+\.\s+)[A-Z].+|\*\*[A-Z][^*]+\*\*)$"
)


def structural_split(text: str) -> list[str]:
    """
    Splits the text into chunks based on structural elements like headers.

    Args:
        text (str): The input text to be split.

    Returns:
        list[str]: A list of text chunks.
    """
    parts = HEADER_PATTERN.split(text)
    headers = HEADER_PATTERN.findall(text)
    segments = []
    for i, part in enumerate(parts):
        header = headers[i - 1] if i > 0 else ""
        combined = (header + "\n" + part).strip()
        if combined:
            sub_parts = [s.strip() for s in combined.split("\n\n") if s.strip()]
            segments.extend(sub_parts)  # extend, not append — sub_parts is already a list

    return segments or [text]


def merge_small_chunks(segments: list[str], min_chars: int = 150) -> list[str]:
    """
    Merges small chunks of text into larger ones based on a minimum length.

    Args:
        segments (list[str]): A list of text chunks to be merged.
        min_chars (int): Chunks shorter than this are merged into the previous one.

    Returns:
        list[str]: A list of merged text chunks.
    """
    merged_chunks = []
    current_chunk = ""

    for chunk in segments:  # was: `chunks` (undefined) — fixed to `segments`
        if len(current_chunk) + len(chunk) + 1 <= min_chars:  # was: `min_length` (undefined)
            current_chunk += " " + chunk if current_chunk else chunk
        else:
            if current_chunk:
                merged_chunks.append(current_chunk.strip())
            current_chunk = chunk

    if current_chunk:
        merged_chunks.append(current_chunk.strip())

    return merged_chunks


def split_large_chunks(segments: list[str], max_chars: int = 1200) -> list[str]:
    """
    Splits large chunks of text into smaller ones based on a maximum length.

    Args:
        segments (list[str]): A list of text chunks to be split.
        max_chars (int): The maximum length of a chunk before it is split.

    Returns:
        list[str]: A list of split text chunks.
    """
    split_chunks = []

    for chunk in segments:
        if len(chunk) <= max_chars:
            split_chunks.append(chunk)
        else:
            sentences = re.split(r"(?<=[.!?])\s+", chunk)
            current = ""
            for sentence in sentences:
                if len(current) + len(sentence) > max_chars and current:
                    split_chunks.append(current.strip())
                    current = sentence
                else:
                    current += " " + sentence
            if current.strip():
                split_chunks.append(current.strip())

    return split_chunks


# ── Stage 2: Gemini topic labeling ───────────────────────────────────────────

def label_topics_with_gemini(segments: list[str]) -> list[str]:
    """
    Labels each chunk of text with a topic using Gemini.

    Args:
        segments (list[str]): A list of text chunks to be labeled.

    Returns:
        list[str]: A topic label for each segment.
    """
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-2.0-flash")

    numbered = "\n\n".join(f"[{i}] {seg[:300]}" for i, seg in enumerate(segments))
    prompt = f"""You are analyzing a curriculum document.
For each numbered segment below, provide a short topic label (2-5 words, title case).
Return ONLY a JSON object like: {{"0": "Photosynthesis Process", "1": "Plant Cell Structure", ...}}

Segments:
{numbered}"""

    response = model.generate_content(prompt)
    raw = response.text.strip()

    json_match = re.search(r"\{.*\}", raw, re.DOTALL)
    if json_match:
        labels = json.loads(json_match.group())
        return [labels.get(str(i), f"Section {i + 1}") for i in range(len(segments))]

    return [f"Section {i + 1}" for i in range(len(segments))]


# ── Public API ────────────────────────────────────────────────────────────────

def smart_chunker(text: str, source_file: str = "unknown") -> list[Chunk]:
    """
    A smart chunker that combines structural splitting, merging small chunks,
    splitting large chunks, and labeling topics with Gemini.

    Args:
        text (str): The input text to be chunked.
        source_file (str): The name of the source file for metadata.

    Returns:
        list[Chunk]: A list of Chunk objects ready for embedding.
    """
    segments = structural_split(text)
    segments = merge_small_chunks(segments, min_chars=150)
    segments = split_large_chunks(segments, max_chars=1200)
    topics = label_topics_with_gemini(segments)

    return [
        Chunk(
            text=seg,
            topic=topics[i],
            source_file=source_file,
            chunk_index=i,
            char_count=len(seg),
        )
        for i, seg in enumerate(segments)
    ]
