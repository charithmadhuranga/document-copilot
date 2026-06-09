from __future__ import annotations

import json
from typing import AsyncGenerator


async def stream_text(text: str) -> AsyncGenerator[str, None]:
    word_count = max(len(text.split()), 1)
    words = text.split()
    chunk_size = max(1, word_count // 5)

    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i : i + chunk_size])
        yield f"0:{json.dumps(chunk)}\n"

    yield f"0:{json.dumps('[DONE]')}\n"
