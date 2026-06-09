from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from app.database.connection import fetch_rows


def ensure_profile(owner_id: uuid.UUID, email: str) -> None:
    fetch_rows(
        """INSERT INTO profiles (id, email)
           VALUES (%(id)s, %(email)s)
           ON CONFLICT (id) DO NOTHING""",
        {"id": owner_id, "email": email},
    )


def list_threads(owner_id: uuid.UUID) -> list[dict[str, Any]]:
    rows = fetch_rows(
        """SELECT id, title, created_at, updated_at
           FROM chat_threads
           WHERE owner_id = %(owner_id)s
           ORDER BY updated_at DESC""",
        {"owner_id": owner_id},
    )
    return [
        {
            "id": str(r["id"]),
            "title": r["title"],
            "createdAt": r["created_at"].isoformat() if isinstance(r["created_at"], datetime) else r["created_at"],
            "updatedAt": r["updated_at"].isoformat() if isinstance(r["updated_at"], datetime) else r["updated_at"],
        }
        for r in rows
    ]


def create_thread(owner_id: uuid.UUID, title: str = "New Chat") -> dict[str, Any]:
    rows = fetch_rows(
        """INSERT INTO chat_threads (id, owner_id, title)
           VALUES (%(id)s, %(owner_id)s, %(title)s)
           RETURNING id, title, created_at, updated_at""",
        {"id": uuid.uuid4(), "owner_id": owner_id, "title": title},
    )
    r = rows[0]
    return {
        "id": str(r["id"]),
        "title": r["title"],
        "createdAt": r["created_at"].isoformat() if isinstance(r["created_at"], datetime) else r["created_at"],
        "updatedAt": r["updated_at"].isoformat() if isinstance(r["updated_at"], datetime) else r["updated_at"],
    }


def delete_thread(thread_id: uuid.UUID, owner_id: uuid.UUID) -> bool:
    if not _owns_thread(thread_id, owner_id):
        return False
    rows = fetch_rows(
        "DELETE FROM chat_threads WHERE id = %(id)s RETURNING id",
        {"id": thread_id},
    )
    return len(rows) > 0


def get_thread(thread_id: uuid.UUID, owner_id: uuid.UUID) -> dict[str, Any] | None:
    rows = fetch_rows(
        """SELECT id, title, created_at, updated_at
           FROM chat_threads
           WHERE id = %(id)s AND owner_id = %(owner_id)s""",
        {"id": thread_id, "owner_id": owner_id},
    )
    if not rows:
        return None
    r = rows[0]
    return {
        "id": str(r["id"]),
        "title": r["title"],
        "createdAt": r["created_at"].isoformat() if isinstance(r["created_at"], datetime) else r["created_at"],
        "updatedAt": r["updated_at"].isoformat() if isinstance(r["updated_at"], datetime) else r["updated_at"],
    }


def update_thread_title(thread_id: uuid.UUID, owner_id: uuid.UUID, title: str) -> dict[str, Any] | None:
    if not _owns_thread(thread_id, owner_id):
        return None
    rows = fetch_rows(
        """UPDATE chat_threads SET title = %(title)s, updated_at = NOW()
           WHERE id = %(id)s RETURNING id, title, created_at, updated_at""",
        {"id": thread_id, "title": title},
    )
    if not rows:
        return None
    r = rows[0]
    return {
        "id": str(r["id"]),
        "title": r["title"],
        "createdAt": r["created_at"].isoformat() if isinstance(r["created_at"], datetime) else r["created_at"],
        "updatedAt": r["updated_at"].isoformat() if isinstance(r["updated_at"], datetime) else r["updated_at"],
    }


def _owns_thread(thread_id: uuid.UUID, owner_id: uuid.UUID) -> bool:
    rows = fetch_rows(
        "SELECT id FROM chat_threads WHERE id = %(id)s AND owner_id = %(owner_id)s",
        {"id": thread_id, "owner_id": owner_id},
    )
    return len(rows) > 0
