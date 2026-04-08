from datetime import datetime, timezone
from typing import Any

from ..db import get_connection


def list_docs() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, title, slug, created_at, updated_at
            FROM docs
            ORDER BY updated_at DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_doc(doc_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM docs WHERE id = ?", (doc_id,)).fetchone()
    return dict(row) if row else None


def create_doc(title: str, slug: str, content: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO docs (title, slug, content, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (title, slug, content, now, now),
        )
        doc_id = cursor.lastrowid
    return get_doc(doc_id)


def update_doc(doc_id: int, title: str, slug: str, content: str) -> dict[str, Any] | None:
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE docs
            SET title = ?, slug = ?, content = ?, updated_at = ?
            WHERE id = ?
            """,
            (title, slug, content, now, doc_id),
        )
    if cursor.rowcount == 0:
        return None
    return get_doc(doc_id)


def delete_doc(doc_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM docs WHERE id = ?", (doc_id,))
    return cursor.rowcount > 0
