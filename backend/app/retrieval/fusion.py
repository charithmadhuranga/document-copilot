from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(order=True)
class RankedItem:
    score: float = field(compare=True)
    chunk_id: str = field(compare=False)
    source: str = field(compare=False)


def reciprocal_rank_fusion(
    semantic_results: list[tuple[str, float]],
    fulltext_results: list[tuple[str, float]],
    k: int = 60,
    top_n: int = 10,
) -> list[tuple[str, float]]:
    scores: dict[str, float] = {}

    for rank, (chunk_id, _) in enumerate(semantic_results):
        scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank + 1)

    for rank, (chunk_id, _) in enumerate(fulltext_results):
        scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank + 1)

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return ranked[:top_n]
