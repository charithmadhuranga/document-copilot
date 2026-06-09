from __future__ import annotations

from typing import Literal

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


class ChartDataPoint(BaseModel):
    label: str
    value: float
    category: str | None = None


class ChartData(BaseModel):
    chart_type: Literal["bar", "line", "pie"]
    title: str
    data_points: list[ChartDataPoint]
    x_label: str | None = None
    y_label: str | None = None


class GroundedAnswer(BaseModel):
    answer: str
    citations: list[Citation]
    chart: ChartData | None = None
