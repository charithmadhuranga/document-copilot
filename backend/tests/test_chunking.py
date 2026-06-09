from __future__ import annotations

from ingest.chunk import chunk_document


def test_empty_document():
    chunks = chunk_document("")
    assert chunks == []


def test_single_paragraph():
    chunks = chunk_document("Hello world.")
    assert len(chunks) == 1
    assert chunks[0].content == "Hello world."
    assert chunks[0].section is None


def test_section_split():
    md = "# Section One\n\nContent A.\n\n## Subsection\n\nContent B."
    chunks = chunk_document(md)
    assert len(chunks) == 2
    assert chunks[0].section == "Section One"
    assert chunks[1].section == "Subsection"


def test_exact_token_budget():
    text = "word " * 200
    chunks = chunk_document(text, max_tokens=100)
    assert all(c.token_count <= 100 for c in chunks)
    assert len(chunks) > 1


def test_overlap():
    text = " ".join(f"paragraph_{i}" for i in range(50))
    chunks = chunk_document(text, max_tokens=20, overlap_tokens=5)
    assert len(chunks) >= 1
