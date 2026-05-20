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


def get_image_status_rows(image_type: str, today_start: str, last_24h_start: str) -> dict[str, Any]:
    with get_connection() as conn:
        summary_row = conn.execute(
            """
            SELECT
                COUNT(*) AS total_records,
                SUM(CASE WHEN fetched_at >= ? THEN 1 ELSE 0 END) AS added_today,
                SUM(CASE WHEN fetched_at >= ? THEN 1 ELSE 0 END) AS added_last_24h
            FROM images
            WHERE image_type = ?
            """,
            (today_start, last_24h_start, image_type),
        ).fetchone()
        latest_rows = conn.execute(
            """
            SELECT *
            FROM images
            WHERE image_type = ?
            ORDER BY fetched_at DESC, id DESC
            LIMIT 2
            """,
            (image_type,),
        ).fetchall()
        duplicate_row = conn.execute(
            """
            SELECT COALESCE(SUM(url_count - 1), 0) AS duplicate_count
            FROM (
                SELECT image_url, COUNT(*) AS url_count
                FROM images
                WHERE image_type = ? AND image_url IS NOT NULL AND image_url != ''
                GROUP BY image_url
                HAVING COUNT(*) > 1
            )
            """,
            (image_type,),
        ).fetchone()

    return {
        "total_records": summary_row["total_records"] if summary_row else 0,
        "added_today": summary_row["added_today"] if summary_row and summary_row["added_today"] else 0,
        "added_last_24h": summary_row["added_last_24h"] if summary_row and summary_row["added_last_24h"] else 0,
        "latest": dict(latest_rows[0]) if latest_rows else None,
        "previous": dict(latest_rows[1]) if len(latest_rows) > 1 else None,
        "possible_duplicate_count": duplicate_row["duplicate_count"] if duplicate_row else 0,
    }
