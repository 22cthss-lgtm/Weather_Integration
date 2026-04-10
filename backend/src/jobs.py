from .models.image_repository import insert_image
from .services.cwa_service import CWAService
from .services.ocean_service import OceanService
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
        )


def fetch_all_images() -> None:
    for service in get_services():
        save_payloads(service.fetch())


def fetch_satellite_image() -> None:
    save_payloads(CWAService().fetch_satellite())


def fetch_radar_image() -> None:
    save_payloads(CWAService().fetch_radar())


def fetch_temperature_image() -> None:
    save_payloads(CWAService().fetch_temperature())


def fetch_sst_image() -> None:
    save_payloads(OceanService().fetch_sst())


def bootstrap_images() -> None:
    fetch_all_images()
