from __future__ import annotations

import json
from typing import AsyncGenerator

from app.assistant.agent import build_agent
from app.assistant.deps import DocumentAgentDeps
from app.assistant.outputs import GroundedAnswer
from app.grounding.validator import GroundingError, GroundingValidator
from app.retrieval.retriever import DocumentRetriever


async def run_chat_turn(
    thread_id: str,
    messages: list[dict],
    user_id: str = "",
) -> AsyncGenerator[str, None]:
    last_message = messages[-1]["content"] if messages else ""
    retriever = DocumentRetriever()
    validator = GroundingValidator()

    deps = DocumentAgentDeps(
        user_id=user_id,
        thread_id=thread_id,
        retriever=retriever,
    )

    try:
        retrieved_passages = retriever.retrieve(last_message)
        retrieved_chunk_ids = {p.chunk_id for p in retrieved_passages}

        agent = build_agent()
        result = await agent.run(last_message, deps=deps, output_type=GroundedAnswer)
        answer: GroundedAnswer = result.data

        validator.validate(answer, retrieved_chunk_ids)

        for chunk in _split_text(answer.answer):
            yield f"0:{json.dumps(chunk)}\n"

        if answer.citations:
            citations_data = [
                {
                    "index": c.citation_index,
                    "chunkId": c.chunk_id,
                    "excerpt": c.excerpt,
                }
                for c in answer.citations
            ]
            yield f"2:{json.dumps(citations_data)}\n"

    except GroundingError as e:
        error_msg = f"I could not verify the answer against the source documents. {e}"
        for chunk in _split_text(error_msg):
            yield f"0:{json.dumps(chunk)}\n"

    except Exception as e:
        error_msg = f"I encountered an error: {e}"
        for chunk in _split_text(error_msg):
            yield f"0:{json.dumps(chunk)}\n"

    yield f"0:{json.dumps('[DONE]')}\n"


def _split_text(text: str, chunk_size: int = 50) -> list[str]:
    words = text.split()
    return [" ".join(words[i : i + chunk_size]) for i in range(0, len(words), chunk_size)]
