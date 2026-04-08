from typing import Any

from ..db import get_connection


def insert_image(
    image_type: str,
    source: str,
    title: str,
    image_url: str,
    source_url: str,
    fetched_at: str,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO images (image_type, source, title, image_url, source_url, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (image_type, source, title, image_url, source_url, fetched_at),
        )


def get_latest_image(image_type: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT *
            FROM images
            WHERE image_type = ?
            ORDER BY fetched_at DESC
            LIMIT 1
            """,
            (image_type,),
        ).fetchone()
    return dict(row) if row else None


def get_image_history(image_type: str, limit: int = 20) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM images
            WHERE image_type = ?
            ORDER BY fetched_at DESC
            LIMIT ?
            """,
            (image_type, limit),
        ).fetchall()
    return [dict(row) for row in rows]
