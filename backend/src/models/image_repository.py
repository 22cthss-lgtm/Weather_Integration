from typing import Any
import re

from ..db import get_connection

IMAGE_TIME_RE = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}")
TITLE_IMAGE_TIME_SQL = (
    "CASE WHEN substr(title, -16) GLOB "
    "'[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9] [0-9][0-9]:[0-9][0-9]' "
    "THEN substr(title, -16) END"
)
IMAGE_TIME_VALUE_SQL = f"COALESCE(image_time, {TITLE_IMAGE_TIME_SQL})"


def effective_image_time(row: dict[str, Any]) -> str | None:
    image_time = row.get("image_time")
    if image_time:
        return image_time

    title_time = row.get("title", "")[-16:]
    if IMAGE_TIME_RE.fullmatch(title_time):
        return title_time
    return None


def insert_image(
    image_type: str,
    source: str,
    title: str,
    image_url: str,
    source_url: str,
    fetched_at: str,
    image_time: str | None = None,
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
            INSERT INTO images (image_type, source, title, image_url, source_url, fetched_at, image_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (image_type, source, title, image_url, source_url, fetched_at, image_time),
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


def get_latest_image_by_image_time(image_type: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT *
            FROM images
            WHERE image_type = ?
            ORDER BY {IMAGE_TIME_VALUE_SQL} DESC, fetched_at DESC
            LIMIT 1
            """,
            (image_type,),
        ).fetchone()
    return dict(row) if row else None


def get_image_by_url(image_type: str, image_url: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT *
            FROM images
            WHERE image_type = ? AND image_url = ?
            LIMIT 1
            """,
            (image_type, image_url),
        ).fetchone()
    return dict(row) if row else None


def get_image_by_image_time(image_type: str, image_time: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT *
            FROM images
            WHERE image_type = ? AND {IMAGE_TIME_VALUE_SQL} = ?
            LIMIT 1
            """,
            (image_type, image_time),
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


def get_image_history_by_date(image_type: str, image_date: str) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT *
            FROM images
            WHERE image_type = ? AND {IMAGE_TIME_VALUE_SQL} >= ? AND {IMAGE_TIME_VALUE_SQL} < ?
            ORDER BY {IMAGE_TIME_VALUE_SQL} ASC, image_time IS NULL ASC, fetched_at DESC
            """,
            (image_type, f"{image_date} 00:00", f"{image_date} 24:00"),
        ).fetchall()

    history = []
    seen_image_times = set()
    for row in rows:
        image = dict(row)
        row_image_time = effective_image_time(image)
        if row_image_time in seen_image_times:
            continue
        seen_image_times.add(row_image_time)
        history.append(image)
    return history
