from __future__ import annotations

from app.assistant.outputs import GroundedAnswer


class GroundingError(Exception):
    pass


class GroundingValidator:
    def validate(self, answer: GroundedAnswer, retrieved_chunk_ids: set[str]) -> None:
        if not answer.citations and not self._is_insufficient_evidence(answer.answer):
            raise GroundingError("Answer has no citations but does not state insufficient evidence")

        for citation in answer.citations:
            if citation.chunk_id not in retrieved_chunk_ids:
                raise GroundingError(
                    f"Citation {citation.citation_index} references chunk "
                    f"{citation.chunk_id} which was not retrieved"
                )

    def _is_insufficient_evidence(self, answer: str) -> bool:
        lower = answer.lower().strip()
        phrases = [
            "does not contain enough evidence",
            "cannot answer",
            "not enough information",
            "corpus does not contain",
            "insufficient evidence",
            "cannot determine",
        ]
        return any(phrase in lower for phrase in phrases)
