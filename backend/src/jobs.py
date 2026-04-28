from .services.cimss_service import CIMSSService
from .models.image_repository import insert_image
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


def fetch_rainfall_image() -> None:
    save_payloads(CWAService().fetch_rainfall())


def fetch_weather_chart_image() -> None:
    save_payloads(CWAService().fetch_weather_chart())


def fetch_tchp_image() -> None:
    save_payloads(CWAService().fetch_tchp())


def fetch_sst_image() -> None:
    save_payloads(OceanService().fetch_sst())


def fetch_seaice_arctic_images() -> None:
    save_payloads(NSIDCService().fetch())


def fetch_seaice_antarctic_images() -> None:
    save_payloads(NSIDCService().fetch())


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
