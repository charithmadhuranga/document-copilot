from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from app.database.connection import fetch_rows
from ingest.chunk import Chunk


def store_document(
    ticker: str,
    company_name: str,
    filing_type: str,
    filing_date: str,
    report_date: str,
    accession_number: str,
    source_url: str,
    markdown_content: str,
    metadata: dict | None = None,
) -> str:
    doc_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    fetch_rows(
        """INSERT INTO source_documents
           (id, ticker, company_name, filing_type, filing_date, report_date,
            accession_number, source_url, markdown_content, metadata, created_at)
           VALUES (%(id)s, %(ticker)s, %(company_name)s, %(filing_type)s,
                   %(filing_date)s, %(report_date)s, %(accession_number)s,
                   %(source_url)s, %(markdown_content)s, %(metadata)s, %(created_at)s)
           RETURNING id""",
        {
            "id": doc_id,
            "ticker": ticker,
            "company_name": company_name,
            "filing_type": filing_type,
            "filing_date": filing_date,
            "report_date": report_date,
            "accession_number": accession_number,
            "source_url": source_url,
            "markdown_content": markdown_content,
            "metadata": json.dumps(metadata or {}),
            "created_at": now,
        },
    )
    return doc_id


def store_chunks(doc_id: str, chunks: list[Chunk], embeddings: list[list[float]]) -> list[str]:
    chunk_ids: list[str] = []
    now = datetime.now(timezone.utc).isoformat()

    for chunk, embedding in zip(chunks, embeddings, strict=True):
        chunk_id = str(uuid.uuid4())
        chunk_ids.append(chunk_id)

        fetch_rows(
            """INSERT INTO document_chunks
               (id, document_id, chunk_index, section, content,
                token_count, embedding, metadata, created_at)
               VALUES (%(id)s, %(doc_id)s, %(index)s, %(section)s, %(content)s,
                       %(token_count)s, %(embedding)s, %(metadata)s, %(created_at)s)
               RETURNING id""",
            {
                "id": chunk_id,
                "doc_id": doc_id,
                "index": chunk.index,
                "section": chunk.section,
                "content": chunk.content,
                "token_count": chunk.token_count,
                "embedding": embedding,
                "metadata": json.dumps({}),
                "created_at": now,
            },
        )

    return chunk_ids
