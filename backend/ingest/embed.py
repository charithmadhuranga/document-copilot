from __future__ import annotations

from app.embeddings import get_embedding_provider


def generate_embedding(text: str) -> list[float]:
    return get_embedding_provider().generate_embedding(text)
