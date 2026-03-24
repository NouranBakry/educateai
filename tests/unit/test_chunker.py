# pytest discovers this file because its name starts with test_
# pytest discovers each function below because their names start with test_

import textwrap                          # strips leading indentation from multiline strings
from unittest.mock import patch          # replaces a real function with a fake one during a test

from educateai.ingestion.chunker import (
    merge_small_chunks,
    smart_chunker,
    split_large_chunks,
    structural_split,
)


# ── structural_split ──────────────────────────────────────────────────────────
# What we're verifying: given text with markdown headers, the function
# produces one segment per section, each starting with its header line.

def test_structural_split_with_headers():
    # textwrap.dedent removes the leading spaces that Python adds when you
    # write a multiline string inside an indented function. Without it,
    # every line would start with spaces and the header regex wouldn't match.
    text = textwrap.dedent("""\
        # Header 1
        This is some text under header 1.

        ## Header 2
        This is some text under header 2.

        ### Header 3
        This is some text under header 3.
    """)

    chunks = structural_split(text)

    # assert is how pytest checks correctness.
    # If the expression is True → test passes silently.
    # If the expression is False → pytest stops here, prints the values, marks FAILED.
    assert len(chunks) == 3
    assert chunks[0].startswith("# Header 1")
    assert chunks[1].startswith("## Header 2")
    assert chunks[2].startswith("### Header 3")


def test_structural_split_no_headers_returns_whole_text():
    # Verifies the fallback: if no headers found, return the whole text as one chunk.
    text = "Just a plain paragraph with no headers at all."

    chunks = structural_split(text)

    assert len(chunks) == 1
    assert chunks[0] == text


def test_structural_split_double_newline_creates_separate_segments():
    # Verifies that double newlines (blank lines) also act as split points
    # even without headers — important for plain-text PDFs.
    text = textwrap.dedent("""\
        First paragraph here.

        Second paragraph here.

        Third paragraph here.
    """)

    chunks = structural_split(text)

    assert len(chunks) == 3


# ── merge_small_chunks ────────────────────────────────────────────────────────
# What we're verifying: tiny segments below min_chars get glued together;
# large segments stay separate.
# NOTE: this function takes list[str], not a raw string.

def test_merge_small_chunks_combines_tiny_segments():
    # Three short segments (each 2 chars). min_chars=10.
    # 2 + 2 + 1 = 5 <= 10, so they keep accumulating into one.
    segments = ["AB", "CD", "EF"]

    merged = merge_small_chunks(segments, min_chars=10)

    assert len(merged) == 1
    assert "AB" in merged[0]
    assert "CD" in merged[0]
    assert "EF" in merged[0]


def test_merge_small_chunks_keeps_large_segments_separate():
    # Two segments each 30 chars. min_chars=10.
    # 30 + 30 + 1 = 61 > 10, so they can't merge — each becomes its own chunk.
    segments = ["A" * 30, "B" * 30]

    merged = merge_small_chunks(segments, min_chars=10)

    assert len(merged) == 2


# ── split_large_chunks ────────────────────────────────────────────────────────
# What we're verifying: segments above max_chars get split at sentence
# boundaries; segments below max_chars are left untouched.

def test_split_large_chunks_breaks_oversized_segment():
    # "This is a sentence. " repeated 100 times = ~2000 chars.
    # With max_chars=500, it must be split into multiple chunks.
    long_segment = "This is a sentence. " * 100

    result = split_large_chunks([long_segment], max_chars=500)

    assert len(result) > 1                      # was split
    assert all(len(s) <= 600 for s in result)   # no chunk wildly exceeds the limit


def test_split_large_chunks_leaves_short_segment_untouched():
    short_segment = "Short sentence."

    result = split_large_chunks([short_segment], max_chars=500)

    assert result == [short_segment]


# ── smart_chunker ─────────────────────────────────────────────────────────────
# What we're verifying: the full pipeline returns Chunk objects with the right
# metadata. We NEVER call the real Gemini API in unit tests — it's slow,
# costs quota, and makes tests non-deterministic.
#
# `patch` temporarily replaces label_topics_with_gemini with a lambda that
# immediately returns a fixed list. The real function is restored after the
# `with` block exits — other tests are unaffected.

SAMPLE_TEXT = textwrap.dedent("""\
    ## Photosynthesis
    Plants convert sunlight into energy. Chlorophyll absorbs light.
    Carbon dioxide and water produce glucose and oxygen.

    ## Food Chains
    Energy flows through ecosystems via food chains.
    Producers, consumers, and decomposers each play a role.
""")


def test_smart_chunker_returns_chunk_objects():
    with patch(
        "educateai.ingestion.chunker.label_topics_with_gemini",
        return_value=["Photosynthesis Process", "Food Chain Basics"],
    ):
        chunks = smart_chunker(SAMPLE_TEXT, source_file="test.pdf")

    # Verify correct number of chunks and topic labels from the mock
    assert len(chunks) == 2
    assert chunks[0].topic == "Photosynthesis Process"
    assert chunks[1].topic == "Food Chain Basics"


def test_smart_chunker_metadata_is_set_correctly():
    with patch(
        "educateai.ingestion.chunker.label_topics_with_gemini",
        return_value=["Photosynthesis Process", "Food Chain Basics"],
    ):
        chunks = smart_chunker(SAMPLE_TEXT, source_file="biology.pdf")

    for i, chunk in enumerate(chunks):
        assert chunk.source_file == "biology.pdf"   # came from the argument we passed
        assert chunk.chunk_index == i               # 0-based position in document
        assert chunk.char_count == len(chunk.text)  # precomputed length matches actual
        assert chunk.chunk_id                       # uuid was generated (non-empty)


def test_smart_chunker_no_empty_chunks():
    with patch(
        "educateai.ingestion.chunker.label_topics_with_gemini",
        return_value=["Photosynthesis Process", "Food Chain Basics"],
    ):
        chunks = smart_chunker(SAMPLE_TEXT, source_file="test.pdf")

    assert all(len(c.text) > 0 for c in chunks)
