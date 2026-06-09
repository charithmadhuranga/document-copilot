from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SearchResult:
    chunk_id: str
    document_id: str
    score: float


SEMANTIC_SEARCH_SQL = """
SELECT
    c.id AS chunk_id,
    c.document_id,
    1 - (c.embedding <=> %(embedding)s::vector) AS score
FROM document_chunks c
WHERE c.embedding IS NOT NULL
ORDER BY c.embedding <=> %(embedding)s::vector
LIMIT %(limit)s
"""

FULLTEXT_SEARCH_SQL = """
SELECT
    c.id AS chunk_id,
    c.document_id,
    ts_rank(c.search_vector, plainto_tsquery('english', %(query)s)) AS score
FROM document_chunks c
WHERE c.search_vector @@ plainto_tsquery('english', %(query)s)
ORDER BY score DESC
LIMIT %(limit)s
"""

CHUNK_WITH_DOC_SQL = """
SELECT
    c.id AS chunk_id,
    c.chunk_index,
    c.section,
    c.content,
    c.token_count,
    c.metadata,
    d.id AS document_id,
    d.ticker,
    d.company_name,
    d.filing_type,
    d.filing_date,
    d.report_date,
    d.accession_number,
    d.source_url
FROM document_chunks c
JOIN source_documents d ON d.id = c.document_id
WHERE c.id = ANY(%(chunk_ids)s::uuid[])
"""
