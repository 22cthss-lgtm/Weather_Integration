from datetime import date, datetime, timedelta, timezone

from .services.cimss_service import CIMSSService
from .models.image_repository import get_image_by_image_time, get_image_by_url, insert_image
from .services.cwa_service import CWAService
from .services.kma_service import KMAService
from .services.nsidc_service import NSIDCService
from .services.ocean_service import OceanService
from .models.image_repository import get_latest_image
from .services.registry import get_services


def save_payloads(payloads) -> None:
    for payload in payloads:
        insert_image(
            image_type=payload.image_type,
            source=payload.source,
            title=payload.title,
            image_url=payload.image_url,
            source_url=payload.source_url,
            fetched_at=payload.fetched_at,
            image_time=getattr(payload, "image_time", None),
        )


def fetch_all_images() -> None:
    for service in get_services():
        save_payloads(service.fetch())


def fetch_satellite_image() -> None:
    save_payloads(CWAService().fetch_satellite())

def backfill_satellite_images(
    *,
    range_name: str = "today",
    image_date: date | None = None,
    now: datetime | None = None,
) -> dict:
    service = CWAService()
    current_time = now or datetime.now(service.satellite_timezone)
    target_date = image_date or current_time.astimezone(service.satellite_timezone).date()

    if range_name != "today" and image_date is None:
        raise ValueError("Only range=today or an explicit date is supported.")

    slots = service.satellite_time_slots_for_date(target_date, now=current_time)
    summary = {
        "image_type": "satellite",
        "date": target_date.isoformat(),
        "requested": len(slots),
        "inserted": 0,
        "skipped_existing": 0,
        "missing": 0,
        "failed": 0,
    }

    for slot in slots:
        image_time = slot.strftime("%Y-%m-%d %H:%M")
        image_url = service.build_satellite_image_url(slot)
        if get_image_by_image_time("satellite", image_time) or get_image_by_url("satellite", image_url):
            summary["skipped_existing"] += 1
            continue

        try:
            exists = service.image_exists(image_url)
        except Exception:
            summary["failed"] += 1
            continue

        if not exists:
            summary["missing"] += 1
            continue

        insert_image(
            image_type="satellite",
            source=service.source_name,
            title=f"CWA Color Satellite Cloud {image_time}",
            image_url=image_url,
            source_url=service.satellite_source_url,
            fetched_at=datetime.now(timezone.utc).isoformat(),
            image_time=image_time,
        )
        summary["inserted"] += 1

    return summary

def fetch_radar_image() -> None:
    save_payloads(CWAService().fetch_radar())


def backfill_radar_images(
    *,
    range_name: str = "today",
    image_date: date | None = None,
    now: datetime | None = None,
) -> dict:
    service = CWAService()
    current_time = now or datetime.now(service.satellite_timezone)
    target_date = image_date or current_time.astimezone(service.satellite_timezone).date()

    if range_name != "today" and image_date is None:
        raise ValueError("Only range=today or an explicit date is supported.")

    slots = service.radar_time_slots_for_date(target_date, now=current_time)
    summary = {
        "image_type": "radar",
        "date": target_date.isoformat(),
        "requested": len(slots),
        "inserted": 0,
        "skipped_existing": 0,
        "missing": 0,
        "failed": 0,
    }

    for slot in slots:
        image_time = slot.strftime("%Y-%m-%d %H:%M")
        image_url = service.build_radar_image_url(slot)
        if get_image_by_image_time("radar", image_time) or get_image_by_url("radar", image_url):
            summary["skipped_existing"] += 1
            continue

        try:
            exists = service.image_exists(image_url)
        except Exception:
            summary["failed"] += 1
            continue

        if not exists:
            summary["missing"] += 1
            continue

        insert_image(
            image_type="radar",
            source=service.source_name,
            title=f"CWA Radar Echo {image_time}",
            image_url=image_url,
            source_url=service.radar_source_url,
            fetched_at=datetime.now(timezone.utc).isoformat(),
            image_time=image_time,
        )
        summary["inserted"] += 1

    return summary


def fetch_temperature_image() -> None:
    save_payloads(CWAService().fetch_temperature())


def fetch_rainfall_image() -> None:
    save_payloads(CWAService().fetch_rainfall())


def rainfall_daily_representative_slots(target_date: date) -> list[dict]:
    return [
        {
            "label": "Yesterday Full-Day Rainfall",
            "represented_date": (target_date - timedelta(days=1)).isoformat(),
            "image_time": datetime.combine(target_date, datetime.min.time(), tzinfo=CWAService.satellite_timezone),
        },
        {
            "label": "Day Before Yesterday Full-Day Rainfall",
            "represented_date": (target_date - timedelta(days=2)).isoformat(),
            "image_time": datetime.combine(target_date - timedelta(days=1), datetime.min.time(), tzinfo=CWAService.satellite_timezone),
        },
    ]


def backfill_rainfall_images(
    *,
    range_name: str = "today",
    image_date: date | None = None,
    now: datetime | None = None,
) -> dict:
    service = CWAService()
    current_time = now or datetime.now(service.satellite_timezone)
    target_date = image_date or current_time.astimezone(service.satellite_timezone).date()

    if range_name != "today" and image_date is None:
        raise ValueError("Only range=today or an explicit date is supported.")

    slots = service.rainfall_time_slots_for_date(target_date, now=current_time)
    summary = {
        "image_type": "rainfall",
        "date": target_date.isoformat(),
        "requested": len(slots),
        "inserted": 0,
        "skipped_existing": 0,
        "missing": 0,
        "failed": 0,
        "daily_representatives": {
            "requested": 0,
            "inserted": 0,
            "skipped_existing": 0,
            "missing": 0,
            "failed": 0,
        },
    }

    def backfill_slot(slot: datetime, target_summary: dict) -> None:
        image_time = slot.strftime("%Y-%m-%d %H:%M")
        image_url = service.build_rainfall_image_url(slot)
        if get_image_by_image_time("rainfall", image_time) or get_image_by_url("rainfall", image_url):
            target_summary["skipped_existing"] += 1
            return

        try:
            exists = service.image_exists(image_url)
        except Exception:
            target_summary["failed"] += 1
            return

        if not exists:
            target_summary["missing"] += 1
            return

        insert_image(
            image_type="rainfall",
            source=service.source_name,
            title=f"CWA Accumulated Rainfall {image_time}",
            image_url=image_url,
            source_url=service.rainfall_source_url,
            fetched_at=datetime.now(timezone.utc).isoformat(),
            image_time=image_time,
        )
        target_summary["inserted"] += 1

    for slot in slots:
        backfill_slot(slot, summary)

    daily_summary = summary["daily_representatives"]
    daily_slots = rainfall_daily_representative_slots(target_date)
    daily_summary["requested"] = len(daily_slots)
    for daily_slot in daily_slots:
        backfill_slot(daily_slot["image_time"], daily_summary)

    return summary


def fetch_weather_chart_image() -> None:
    save_payloads(CWAService().fetch_weather_chart())


def fetch_tchp_image() -> None:
    save_payloads(CWAService().fetch_tchp())


def fetch_sst_image() -> None:
    save_payloads(OceanService().fetch_sst())


def fetch_seaice_arctic_images() -> None:
    save_payloads(NSIDCService().fetch_arctic())


def fetch_seaice_antarctic_images() -> None:
    save_payloads(NSIDCService().fetch_antarctic())


def fetch_cimss_wind_analysis_images() -> None:
    save_payloads(CIMSSService().fetch_wind_analysis())


def fetch_cimss_steering_flow_images() -> None:
    save_payloads(CIMSSService().fetch_steering_flow())


def fetch_850hpa_image() -> None:
    latest_image = get_latest_image("850hpa")
    payloads = list(KMAService().fetch_850hpa())

    for payload in payloads:
        if latest_image and latest_image["image_url"] == payload.image_url:
            continue

        insert_image(
            image_type=payload.image_type,
            source=payload.source,
            title=payload.title,
            image_url=payload.image_url,
            source_url=payload.source_url,
            fetched_at=payload.fetched_at,
        )


def bootstrap_images() -> None:
    fetch_all_images()
