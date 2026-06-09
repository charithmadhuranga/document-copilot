from __future__ import annotations

from dataclasses import dataclass

from app.database.connection import fetch_rows
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.queries import CHUNK_WITH_DOC_SQL, FULLTEXT_SEARCH_SQL, SEMANTIC_SEARCH_SQL
from ingest.embed import generate_embedding


@dataclass
class Passage:
    chunk_id: str
    content: str
    section: str | None
    token_count: int
    score: float
    document_id: str
    ticker: str
    company_name: str
    filing_type: str
    filing_date: str
    source_url: str


class DocumentRetriever:
    def retrieve(self, query: str, top_n: int = 10) -> list[Passage]:
        embedding = generate_embedding(query)

        semantic = self._run_semantic_search(embedding, top_n * 3)
        fulltext = self._run_fulltext_search(query, top_n * 3)

        fused = reciprocal_rank_fusion(semantic, fulltext, top_n=top_n)
        fused_ids = [cid for cid, _ in fused]
        if not fused_ids:
            return []

        passages = self._fetch_passages(fused_ids)
        score_map = dict(fused)

        for p in passages:
            p.score = score_map.get(p.chunk_id, 0.0)

        passages.sort(key=lambda p: p.score, reverse=True)
        return passages

    def _run_semantic_search(
        self, embedding: list[float], limit: int
    ) -> list[tuple[str, float]]:
        rows = fetch_rows(
            SEMANTIC_SEARCH_SQL,
            {"embedding": embedding, "limit": limit},
        )
        return [(r["chunk_id"], float(r["score"])) for r in rows]

    def _run_fulltext_search(
        self, query: str, limit: int
    ) -> list[tuple[str, float]]:
        rows = fetch_rows(
            FULLTEXT_SEARCH_SQL,
            {"query": query, "limit": limit},
        )
        return [(r["chunk_id"], float(r["score"])) for r in rows]

    def _fetch_passages(self, chunk_ids: list[str]) -> list[Passage]:
        rows = fetch_rows(
            CHUNK_WITH_DOC_SQL,
            {"chunk_ids": chunk_ids},
        )
        return [
            Passage(
                chunk_id=r["chunk_id"],
                content=r["content"],
                section=r.get("section"),
                token_count=r["token_count"],
                score=0.0,
                document_id=r["document_id"],
                ticker=r["ticker"],
                company_name=r["company_name"],
                filing_type=r["filing_type"],
                filing_date=r["filing_date"],
                source_url=r["source_url"],
            )
            for r in rows
        ]
