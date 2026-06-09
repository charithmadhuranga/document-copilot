from __future__ import annotations

from collections.abc import Sequence
from contextlib import contextmanager
from typing import Any

import psycopg2
import psycopg2.extras
from psycopg2 import ProgrammingError

from app.config import get_settings


@contextmanager
def get_db():
    settings = get_settings()
    conn = psycopg2.connect(settings.database_url)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute(sql: str, params: dict[str, Any] | None = None) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or {})


def fetch_rows(sql: str, params: dict[str, Any] | None = None) -> Sequence[dict[str, Any]]:
    with get_db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params or {})
            try:
                return cur.fetchall()
            except ProgrammingError:
                return []
