from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from ..config import IMAGE_TYPE_TTL_MINUTES
from ..models.image_repository import effective_image_time, get_image_status_rows


STATUS_TIMEZONE = ZoneInfo("Asia/Taipei")
STATUS_IMAGE_TYPES = [
    "satellite",
    "radar",
    "temperature",
    "rainfall",
    "weather_chart",
    "850hpa",
    "tchp",
    "sst",
    "seaice_arctic_extent",
    "seaice_arctic_concentration",
    "seaice_arctic_timeseries",
    "seaice_antarctic_extent",
    "seaice_antarctic_concentration",
    "seaice_antarctic_timeseries",
    "cimss_wind_shear",
    "cimss_850mb_vorticity",
    "cimss_steering_flow_700_850mb",
    "cimss_steering_flow_500_850mb",
    "cimss_steering_flow_400_850mb",
    "cimss_steering_flow_300_850mb",
    "cimss_steering_flow_250_850mb",
    "cimss_steering_flow_200_700mb",
]

SOURCE_BY_IMAGE_TYPE = {
    "satellite": "CWA",
    "radar": "CWA",
    "temperature": "CWA",
    "rainfall": "CWA",
    "weather_chart": "CWA",
    "850hpa": "KMA",
    "tchp": "CWA",
    "sst": "JMA",
    "seaice_arctic_extent": "NSIDC",
    "seaice_arctic_concentration": "NSIDC",
    "seaice_arctic_timeseries": "NSIDC",
    "seaice_antarctic_extent": "NSIDC",
    "seaice_antarctic_concentration": "NSIDC",
    "seaice_antarctic_timeseries": "NSIDC",
    "cimss_wind_shear": "CIMSS",
    "cimss_850mb_vorticity": "CIMSS",
    "cimss_steering_flow_700_850mb": "CIMSS",
    "cimss_steering_flow_500_850mb": "CIMSS",
    "cimss_steering_flow_400_850mb": "CIMSS",
    "cimss_steering_flow_300_850mb": "CIMSS",
    "cimss_steering_flow_250_850mb": "CIMSS",
    "cimss_steering_flow_200_700mb": "CIMSS",
}


def parse_utc_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def freshness_status(
    image_type: str,
    latest_fetched_at: str | None,
    now: datetime,
) -> tuple[str, str | None]:
    if latest_fetched_at is None:
        return "No Data", "No records found for this image_type."

    fetched_at = parse_utc_datetime(latest_fetched_at)
    if fetched_at is None:
        return "Unknown", "latest_fetched_at is missing or invalid."

    ttl_minutes = IMAGE_TYPE_TTL_MINUTES.get(image_type)
    if ttl_minutes is None:
        return "Unknown", "No explicit TTL configured for this image_type."

    if now - fetched_at <= timedelta(minutes=ttl_minutes):
        return "Fresh", None
    return "Stale", f"Latest fetch is older than configured TTL ({ttl_minutes} minutes)."


def build_status_item(image_type: str, now: datetime) -> dict[str, Any]:
    today_start = (
        now.astimezone(STATUS_TIMEZONE)
        .replace(hour=0, minute=0, second=0, microsecond=0)
        .astimezone(timezone.utc)
        .isoformat()
    )
    last_24h_start = (now - timedelta(hours=24)).isoformat()
    rows = get_image_status_rows(image_type, today_start, last_24h_start)
    latest = rows["latest"]
    previous = rows["previous"]

    latest_fetched_at = latest.get("fetched_at") if latest else None
    status, status_note = freshness_status(image_type, latest_fetched_at, now)
    latest_data_time = effective_image_time(latest) if latest else None
    previous_image_url = previous.get("image_url") if previous else None
    latest_image_url = latest.get("image_url") if latest else None
    latest_url_same_as_previous = None
    if latest_image_url and previous_image_url:
        latest_url_same_as_previous = latest_image_url == previous_image_url

    notes = [status_note] if status_note else []
    if latest and not latest_data_time:
        notes.append("latest_data_time could not be parsed from image_time or title.")
    if latest_url_same_as_previous:
        notes.append("Latest URL matches previous record.")
    if rows["possible_duplicate_count"] > 0:
        notes.append("One or more image_url values appear more than once.")

    return {
        "image_type": image_type,
        "source": (latest.get("source") if latest else None) or SOURCE_BY_IMAGE_TYPE.get(image_type),
        "total_records": rows["total_records"],
        "added_today": rows["added_today"],
        "added_last_24h": rows["added_last_24h"],
        "latest_title": latest.get("title") if latest else None,
        "latest_image_url": latest_image_url,
        "latest_fetched_at": latest_fetched_at,
        "latest_data_time": latest_data_time,
        "previous_image_url": previous_image_url,
        "latest_url_same_as_previous": latest_url_same_as_previous,
        "possible_duplicate_count": rows["possible_duplicate_count"],
        "freshness_status": status,
        "note": " ".join(notes) if notes else None,
    }


def build_image_status_summaries(
    image_types: list[str] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    now = now.astimezone(timezone.utc)

    items = [build_status_item(image_type, now) for image_type in (image_types or STATUS_IMAGE_TYPES)]
    return {
        "generated_at": now.isoformat(),
        "today_timezone": str(STATUS_TIMEZONE),
        "items": items,
    }
