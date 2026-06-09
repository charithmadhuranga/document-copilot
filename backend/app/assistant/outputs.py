from __future__ import annotations

from pydantic import BaseModel


class SourcePassage(BaseModel):
    chunk_id: str
    content: str
    section: str | None = None
    document_id: str = ""
    ticker: str = ""
    company_name: str = ""
    filing_type: str = ""
    filing_date: str = ""
    source_url: str = ""


class Citation(BaseModel):
    citation_index: int
    chunk_id: str
    excerpt: str


class GroundedAnswer(BaseModel):
    answer: str
    citations: list[Citation]
