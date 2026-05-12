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
        latest_row = conn.execute(
            """
            SELECT title, image_url
            FROM images
            WHERE image_type = ?
            ORDER BY fetched_at DESC
            LIMIT 1
            """,
            (image_type,),
        ).fetchone()
        if latest_row and latest_row["title"] == title and latest_row["image_url"] == image_url:
            return

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


def get_latest_image_excluding_prefixes(image_type: str, excluded_prefixes: list[str]) -> dict[str, Any] | None:
    where_parts = ["image_type = ?"]
    params: list[Any] = [image_type]

    for prefix in excluded_prefixes:
        where_parts.append("image_url NOT LIKE ?")
        params.append(f"{prefix}%")

    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT *
            FROM images
            WHERE {' AND '.join(where_parts)}
            ORDER BY fetched_at DESC
            LIMIT 1
            """,
            params,
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
