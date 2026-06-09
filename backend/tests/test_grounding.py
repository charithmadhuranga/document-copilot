from __future__ import annotations

import pytest

from app.assistant.outputs import Citation, GroundedAnswer, SourcePassage
from app.grounding.validator import GroundingError, GroundingValidator


@pytest.fixture
def validator() -> GroundingValidator:
    return GroundingValidator()


def test_valid_answer_with_citations(validator: GroundingValidator) -> None:
    answer = GroundedAnswer(
        answer="Revenue grew 10% in 2024.",
        citations=[Citation(citation_index=0, chunk_id="chunk_1", excerpt="Revenue grew 10%")],
        cited_passages=[
            SourcePassage(
                chunk_id="chunk_1",
                content="Revenue grew 10%",
                document_id="doc_1",
                ticker="AAPL",
                company_name="Apple",
                filing_type="10-K",
                filing_date="2024-01-01",
                source_url="https://example.com",
            )
        ],
    )
    validator.validate(answer, {"chunk_1"})


def test_fails_when_no_citations(validator: GroundingValidator) -> None:
    answer = GroundedAnswer(
        answer="Revenue grew 10%.",
        citations=[],
        cited_passages=[],
    )
    with pytest.raises(GroundingError, match="Answer has no citations"):
        validator.validate(answer, set())


def test_insufficient_evidence_allowed(validator: GroundingValidator) -> None:
    answer = GroundedAnswer(
        answer="The corpus does not contain enough evidence to answer this question.",
        citations=[],
        cited_passages=[],
    )
    validator.validate(answer, set())


def test_fails_on_unretrieved_chunk(validator: GroundingValidator) -> None:
    answer = GroundedAnswer(
        answer="Revenue grew.",
        citations=[Citation(citation_index=0, chunk_id="unknown_chunk", excerpt="...")],
        cited_passages=[
            SourcePassage(
                chunk_id="unknown_chunk",
                content="...",
                document_id="doc_1",
                ticker="AAPL",
                company_name="Apple",
                filing_type="10-K",
                filing_date="2024-01-01",
                source_url="https://example.com",
            )
        ],
    )
    with pytest.raises(GroundingError, match="was not retrieved"):
        validator.validate(answer, {"actual_chunk"})


def test_insufficient_evidence_phrases(validator: GroundingValidator) -> None:
    phrases = [
        "I cannot answer this based on the available documents.",
        "There is insufficient evidence in the corpus.",
        "The corpus does not contain information about that.",
    ]
    for phrase in phrases:
        answer = GroundedAnswer(answer=phrase, citations=[], cited_passages=[])
        validator.validate(answer, set())
