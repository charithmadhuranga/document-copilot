from __future__ import annotations

import uuid
from datetime import datetime, timezone


class Message:
    def __init__(
        self,
        id: str,
        role: str,
        content: str,
        created_at: str | None = None,
    ) -> None:
        self.id = id
        self.role = role
        self.content = content
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    @classmethod
    def from_ai_sdk(cls, msg: dict) -> Message:
        return cls(
            id=msg.get("id", str(uuid.uuid4())),
            role=msg.get("role", "user"),
            content=msg.get("content", ""),
            created_at=msg.get("createdAt"),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "createdAt": self.created_at,
        }
