from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Any, AsyncGenerator

logger = logging.getLogger(__name__)

from app.assistant.agent import build_agent
from app.assistant.deps import DocumentAgentDeps
from app.assistant.outputs import GroundedAnswer
from app.database.message_repo import create_message, save_citations
from app.grounding.validator import GroundingError, GroundingValidator
from app.retrieval.retriever import DocumentRetriever

SSE_EVENT = "data: {}\n\n"
TEXT_ID = "text-0"


def _sse(obj: Any) -> str:
    return SSE_EVENT.format(json.dumps(obj, default=str))


def _extract_text(msg: dict[str, Any]) -> str:
    if "content" in msg and msg["content"]:
        return msg["content"]
    parts = msg.get("parts", [])
    for p in parts:
        if isinstance(p, dict) and p.get("type") == "text":
            return p.get("text", "")
    return ""


def _format_history(messages: list[dict]) -> str:
    lines: list[str] = []
    for msg in messages[:-1]:
        role = msg.get("role", "unknown")
        text = _extract_text(msg)
        if text.strip():
            lines.append(f"[{role}]: {text.strip()}")
    return "\n".join(lines)


async def run_chat_turn(
    thread_id: str,
    messages: list[dict],
    user_id: str = "",
) -> AsyncGenerator[str, None]:
    last_message = _extract_text(messages[-1]) if messages else ""
    message_history = _format_history(messages) if len(messages) > 1 else ""
    retriever = DocumentRetriever()
    validator = GroundingValidator()

    deps = DocumentAgentDeps(
        user_id=user_id,
        thread_id=thread_id,
        retriever=retriever,
        message_history=message_history,
    )

    thread_uuid = uuid.UUID(thread_id)

    yield _sse({"type": "start", "messageId": thread_id})
    yield _sse({"type": "start-step"})
    yield _sse({"type": "text-start", "id": TEXT_ID})

    try:
        retrieved_passages = retriever.retrieve(last_message)
        retrieved_chunk_ids = {p.chunk_id for p in retrieved_passages}

        agent = build_agent()
        try:
            result = await agent.run(last_message, deps=deps)
        except Exception:
            await asyncio.sleep(1)
            result = await agent.run(last_message, deps=deps)
        answer: GroundedAnswer = result.output

        cited_ids = {c.chunk_id for c in answer.citations}
        validator.validate(answer, retrieved_chunk_ids | cited_ids)

        for chunk in _split_text(answer.answer):
            yield _sse({"type": "text-delta", "id": TEXT_ID, "delta": chunk})

        yield _sse({"type": "text-end", "id": TEXT_ID})

        if answer.citations:
            for c in answer.citations:
                yield _sse({
                    "type": "data-citations",
                    "data": {
                        "index": c.citation_index,
                        "chunkId": str(c.chunk_id),
                        "excerpt": c.excerpt,
                    },
                })

        if answer.chart:
            yield _sse({
                "type": "data-chart",
                "data": {
                    "chartType": answer.chart.chart_type,
                    "title": answer.chart.title,
                    "dataPoints": [
                        {
                            "label": dp.label,
                            "value": dp.value,
                            "category": dp.category,
                        }
                        for dp in answer.chart.data_points
                    ],
                    "xLabel": answer.chart.x_label,
                    "yLabel": answer.chart.y_label,
                },
            })

        citation_data = [
            {
                "index": c.citation_index,
                "chunkId": str(c.chunk_id),
                "excerpt": c.excerpt,
            }
            for c in (answer.citations or [])
        ]

        try:
            create_message(thread_uuid, "user", last_message)
            msg = create_message(
                thread_uuid,
                "assistant",
                answer.answer,
                metadata={"citations": citation_data} if citation_data else None,
            )
            if citation_data:
                save_citations(uuid.UUID(msg["id"]), citation_data)
        except Exception as e:
            logger.warning("Failed to persist messages: %s", e)

    except GroundingError as e:
        error_msg = f"I could not verify the answer against the source documents. {e}"
        for chunk in _split_text(error_msg):
            yield _sse({"type": "text-delta", "id": TEXT_ID, "delta": chunk})
        yield _sse({"type": "text-end", "id": TEXT_ID})

    except Exception as e:
        error_msg = f"I encountered an error: {e}"
        for chunk in _split_text(error_msg):
            yield _sse({"type": "text-delta", "id": TEXT_ID, "delta": chunk})
        yield _sse({"type": "text-end", "id": TEXT_ID})

    yield _sse({"type": "finish-step"})
    yield _sse({"type": "finish", "finishReason": "stop"})


def _split_text(text: str) -> list[str]:
    return [text[i:i + 2] for i in range(0, len(text), 2)]
