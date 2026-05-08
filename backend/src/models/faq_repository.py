import json
from datetime import datetime, timezone
from typing import Any

from ..db import get_connection


def _serialize_faq(row) -> dict[str, Any]:
    faq = dict(row)
    faq["tags"] = json.loads(faq["tags"]) if faq.get("tags") else []
    faq["is_pinned"] = bool(faq["is_pinned"])
    return faq


def list_faqs(category: str | None = None, query: str | None = None, pinned: bool | None = None) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []

    if category:
        clauses.append("category = ?")
        params.append(category)

    if query:
        like_query = f"%{query}%"
        clauses.append("(title LIKE ? OR summary LIKE ? OR content LIKE ? OR tags LIKE ?)")
        params.extend([like_query, like_query, like_query, like_query])

    if pinned is not None:
        clauses.append("is_pinned = ?")
        params.append(1 if pinned else 0)

    where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT id, category, title, summary, content, tags, is_pinned, created_at, updated_at
            FROM faqs
            {where_clause}
            ORDER BY is_pinned DESC, updated_at DESC, id DESC
            """,
            params,
        ).fetchall()

    return [_serialize_faq(row) for row in rows]


def get_faq(faq_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM faqs WHERE id = ?", (faq_id,)).fetchone()
    return _serialize_faq(row) if row else None


def ensure_category(name: str) -> None:
    normalized_name = name.strip()
    if not normalized_name:
        return

    now = datetime.now(timezone.utc).isoformat()

    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM faq_categories WHERE name = ?",
            (normalized_name,),
        ).fetchone()
        if existing:
            return

        max_sort_order_row = conn.execute(
            "SELECT COALESCE(MAX(sort_order), 0) AS max_sort_order FROM faq_categories"
        ).fetchone()
        next_sort_order = int(max_sort_order_row["max_sort_order"]) + 1
        conn.execute(
            """
            INSERT INTO faq_categories (name, sort_order, created_at)
            VALUES (?, ?, ?)
            """,
            (normalized_name, next_sort_order, now),
        )


def list_categories() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, name, sort_order, created_at
            FROM faq_categories AS category
            WHERE EXISTS (
                SELECT 1
                FROM faqs AS faq
                WHERE faq.category = category.name
            )
            ORDER BY sort_order ASC, name ASC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def create_faq(
    category: str,
    title: str,
    summary: str,
    content: str,
    tags: list[str] | None,
    is_pinned: bool,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    normalized_tags = [tag.strip() for tag in (tags or []) if tag.strip()]

    ensure_category(category)

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO faqs (category, title, summary, content, tags, is_pinned, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                category.strip(),
                title.strip(),
                summary.strip(),
                content.strip(),
                json.dumps(normalized_tags),
                int(is_pinned),
                now,
                now,
            ),
        )
        faq_id = cursor.lastrowid
    return get_faq(faq_id)


def update_faq(
    faq_id: int,
    category: str,
    title: str,
    summary: str,
    content: str,
    tags: list[str] | None,
    is_pinned: bool,
) -> dict[str, Any] | None:
    now = datetime.now(timezone.utc).isoformat()
    normalized_tags = [tag.strip() for tag in (tags or []) if tag.strip()]

    ensure_category(category)

    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE faqs
            SET category = ?, title = ?, summary = ?, content = ?, tags = ?, is_pinned = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                category.strip(),
                title.strip(),
                summary.strip(),
                content.strip(),
                json.dumps(normalized_tags),
                int(is_pinned),
                now,
                faq_id,
            ),
        )

    if cursor.rowcount == 0:
        return None
    return get_faq(faq_id)


def delete_faq(faq_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM faqs WHERE id = ?", (faq_id,))
    return cursor.rowcount > 0
