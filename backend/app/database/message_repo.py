from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from app.database.connection import fetch_rows


def save_citations(message_id: uuid.UUID, citations: list[dict[str, Any]]) -> None:
    if not citations:
        return
    for c in citations:
        fetch_rows(
            """INSERT INTO message_citations (id, message_id, chunk_id, citation_index, excerpt)
               VALUES (%(id)s, %(message_id)s, %(chunk_id)s, %(index)s, %(excerpt)s)""",
            {
                "id": uuid.uuid4(),
                "message_id": message_id,
                "chunk_id": c.get("chunkId"),
                "index": c.get("index", 0),
                "excerpt": c.get("excerpt", ""),
            },
        )


def list_messages(thread_id: uuid.UUID, owner_id: uuid.UUID) -> list[dict[str, Any]]:
    rows = fetch_rows(
        """SELECT cm.id, cm.role, cm.content, cm.metadata, cm.created_at
           FROM chat_messages cm
           JOIN chat_threads ct ON ct.id = cm.thread_id
           WHERE cm.thread_id = %(thread_id)s AND ct.owner_id = %(owner_id)s
           ORDER BY cm.created_at ASC""",
        {"thread_id": thread_id, "owner_id": owner_id},
    )
    return [
        {
            "id": str(r["id"]),
            "role": r["role"],
            "content": r["content"],
            "metadata": r["metadata"],
            "createdAt": r["created_at"].isoformat() if isinstance(r["created_at"], datetime) else r["created_at"],
        }
        for r in rows
    ]


def create_message(
    thread_id: uuid.UUID,
    role: str,
    content: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rows = fetch_rows(
        """INSERT INTO chat_messages (id, thread_id, role, content, metadata)
           VALUES (%(id)s, %(thread_id)s, %(role)s, %(content)s, %(metadata)s)
           RETURNING id, role, content, metadata, created_at""",
        {
            "id": uuid.uuid4(),
            "thread_id": thread_id,
            "role": role,
            "content": content,
            "metadata": metadata,
        },
    )
    r = rows[0]
    return {
        "id": str(r["id"]),
        "role": r["role"],
        "content": r["content"],
        "metadata": r["metadata"],
        "createdAt": r["created_at"].isoformat() if isinstance(r["created_at"], datetime) else r["created_at"],
    }
