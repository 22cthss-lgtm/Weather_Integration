import re
from datetime import date, datetime, timedelta, timezone

from flask import Blueprint, jsonify, request

from ..config import DEFAULT_IMAGE_TTL_MINUTES, IMAGE_TYPE_TTL_MINUTES
from ..jobs import (
    fetch_cimss_steering_flow_images,
    fetch_cimss_wind_analysis_images,
    fetch_850hpa_image,
    backfill_rainfall_images,
    rainfall_daily_representative_slots,
    fetch_radar_image,
    fetch_rainfall_image,
    fetch_seaice_arctic_images,
    fetch_seaice_antarctic_images,
    fetch_satellite_image,
    fetch_sst_image,
    fetch_temperature_image,
    fetch_tchp_image,
    fetch_weather_chart_image,
)
from ..models.image_repository import (
    get_image_history,
    get_image_history_by_date,
    get_image_by_image_time,
    get_latest_image,
    get_latest_image_by_image_time,
    get_latest_image_excluding_prefixes,
)
from ..services.status_service import build_image_status_summaries


images_bp = Blueprint("images", __name__)
image_time_regex = re.compile(r"(?P<image_time>\d{4}-\d{2}-\d{2} \d{2}:\d{2})$")
image_types_with_embedded_time = {
    "satellite",
    "radar",
    "temperature",
    "rainfall",
    "850hpa",
    "weather_chart",
    "tchp",
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
}
grouped_image_types = {
    "seaice_arctic": ["seaice_arctic_extent", "seaice_arctic_concentration", "seaice_arctic_timeseries"],
    "seaice_antarctic": [
        "seaice_antarctic_extent",
        "seaice_antarctic_concentration",
        "seaice_antarctic_timeseries",
    ],
    "cimss_wind_analysis": ["cimss_wind_shear", "cimss_850mb_vorticity"],
    "cimss_steering_flow": [
        "cimss_steering_flow_700_850mb",
        "cimss_steering_flow_500_850mb",
        "cimss_steering_flow_400_850mb",
        "cimss_steering_flow_300_850mb",
        "cimss_steering_flow_250_850mb",
        "cimss_steering_flow_200_700mb",
    ],
}
REFRESH_IMAGE_FETCHERS = {
    "radar": "fetch_radar_image",
    "satellite": "fetch_satellite_image",
    "temperature": "fetch_temperature_image",
    "rainfall": "fetch_rainfall_image",
}


@images_bp.get("/status")
def image_status():
    return jsonify(build_image_status_summaries())


@images_bp.post("/refresh")
def refresh_image():
    image_type = request.args.get("type", "").strip()
    if not image_type:
        return jsonify({"error": "Query parameter 'type' is required."}), 400

    fetcher_name = REFRESH_IMAGE_FETCHERS.get(image_type)
    if fetcher_name is None:
        return jsonify({"error": "Refresh is not supported for this image type."}), 400

    try:
        fetcher = globals()[fetcher_name]
        fetcher()
    except Exception:
        return jsonify({"error": f"Failed to refresh {image_type} image."}), 502

    return jsonify({"image_type": image_type, "status": "refreshed"})


def parse_fetched_at(fetched_at: str | None) -> datetime | None:
    if not fetched_at:
        return None

    try:
        parsed = datetime.fromisoformat(fetched_at)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def ttl_for_image_type(image_type: str | None) -> timedelta:
    ttl_minutes = IMAGE_TYPE_TTL_MINUTES.get(image_type or "", DEFAULT_IMAGE_TTL_MINUTES)
    return timedelta(minutes=ttl_minutes)


def is_fresh_image(image: dict | None) -> bool:
    fetched_at = parse_fetched_at(image.get("fetched_at") if image else None)
    if fetched_at is None:
        return False
    return datetime.now(timezone.utc) - fetched_at <= ttl_for_image_type(image.get("image_type"))


def latest_records_for_request(image_type: str) -> list[dict] | None:
    child_image_types = grouped_image_types.get(image_type)
    if child_image_types is not None:
        images = [get_latest_image(child_image_type) for child_image_type in child_image_types]
        if any(image is None for image in images):
            return None
        return [image for image in images if image is not None]

    if image_type == "rainfall":
        image = get_latest_image_by_image_time(image_type)
    else:
        image = get_latest_image(image_type)
    if image is None:
        return None
    return [image]


def should_fetch_latest_image(image_type: str) -> bool:
    latest_records = latest_records_for_request(image_type)
    if latest_records is None:
        return True
    return not all(is_fresh_image(image) for image in latest_records)


def serialize_image(image: dict) -> dict:
    serialized = dict(image)
    if serialized.get("image_time"):
        return serialized

    if serialized.get("image_type") in image_types_with_embedded_time:
        match = image_time_regex.search(serialized.get("title", ""))
        if match:
            serialized["image_time"] = match.group("image_time")
        elif serialized.get("image_type") == "weather_chart" and serialized.get("fetched_at"):
            fetched_at = datetime.fromisoformat(serialized["fetched_at"])
            serialized["image_time"] = fetched_at.strftime("%Y-%m-%d %H:%M")
    return serialized


def serialize_seaice_arctic_payload() -> dict | None:
    return serialize_grouped_payload(
        aggregate_type="seaice_arctic",
        source="NSIDC",
        image_types=["seaice_arctic_extent", "seaice_arctic_concentration", "seaice_arctic_timeseries"],
    )


def serialize_grouped_payload(*, aggregate_type: str, source: str, image_types: list[str]) -> dict | None:
    images = [get_latest_image(image_type) for image_type in image_types]

    if any(image is None for image in images):
        return None

    serialized_images = [serialize_image(image) for image in images if image is not None]
    primary_image = serialized_images[0]
    return {
        "image_type": aggregate_type,
        "source": source,
        "title": primary_image["title"],
        "image_url": primary_image["image_url"],
        "source_url": primary_image["source_url"],
        "fetched_at": primary_image["fetched_at"],
        "image_time": primary_image.get("image_time"),
        "images": serialized_images,
    }


def serialize_seaice_antarctic_payload() -> dict | None:
    return serialize_grouped_payload(
        aggregate_type="seaice_antarctic",
        source="NSIDC",
        image_types=[
            "seaice_antarctic_extent",
            "seaice_antarctic_concentration",
            "seaice_antarctic_timeseries",
        ],
    )


def serialize_cimss_wind_analysis_payload() -> dict | None:
    return serialize_grouped_payload(
        aggregate_type="cimss_wind_analysis",
        source="CIMSS",
        image_types=["cimss_wind_shear", "cimss_850mb_vorticity"],
    )


def serialize_cimss_steering_flow_payload() -> dict | None:
    images = [
        get_latest_image("cimss_steering_flow_700_850mb"),
        get_latest_image("cimss_steering_flow_500_850mb"),
        get_latest_image("cimss_steering_flow_400_850mb"),
        get_latest_image("cimss_steering_flow_300_850mb"),
        get_latest_image("cimss_steering_flow_250_850mb"),
        get_latest_image("cimss_steering_flow_200_700mb"),
    ]
    if any(image is None for image in images):
        return None

    serialized_images = [serialize_image(image) for image in images if image is not None]
    primary_image = serialized_images[4]
    return {
        "image_type": "cimss_steering_flow",
        "source": "CIMSS",
        "title": primary_image["title"],
        "image_url": primary_image["image_url"],
        "source_url": primary_image["source_url"],
        "fetched_at": primary_image["fetched_at"],
        "image_time": primary_image.get("image_time"),
        "images": serialized_images,
    }


@images_bp.get("/latest")
def latest_image():
    image_type = request.args.get("type", "").strip()
    if not image_type:
        return jsonify({"error": "Query parameter 'type' is required."}), 400

    if should_fetch_latest_image(image_type):
        if image_type == "satellite":
            fetch_satellite_image()
        elif image_type == "radar":
            fetch_radar_image()
        elif image_type == "temperature":
            fetch_temperature_image()
        elif image_type == "rainfall":
            fetch_rainfall_image()
        elif image_type == "weather_chart":
            fetch_weather_chart_image()
        elif image_type == "tchp":
            fetch_tchp_image()
        elif image_type == "sst":
            fetch_sst_image()
        elif image_type == "850hpa":
            fetch_850hpa_image()
        elif image_type == "seaice_arctic":
            fetch_seaice_arctic_images()
        elif image_type == "seaice_antarctic":
            fetch_seaice_antarctic_images()
        elif image_type == "cimss_wind_analysis":
            fetch_cimss_wind_analysis_images()
        elif image_type == "cimss_steering_flow":
            fetch_cimss_steering_flow_images()

    if image_type == "seaice_arctic":
        image = serialize_seaice_arctic_payload()
        if image is None:
            return jsonify({"error": "Image type not found."}), 404
        return jsonify(image)
    if image_type == "seaice_antarctic":
        image = serialize_seaice_antarctic_payload()
        if image is None:
            return jsonify({"error": "Image type not found."}), 404
        return jsonify(image)
    if image_type == "cimss_wind_analysis":
        image = serialize_cimss_wind_analysis_payload()
        if image is None:
            return jsonify({"error": "Image type not found."}), 404
        return jsonify(image)
    if image_type == "cimss_steering_flow":
        image = serialize_cimss_steering_flow_payload()
        if image is None:
            return jsonify({"error": "Image type not found."}), 404
        return jsonify(image)

    if image_type == "radar":
        image = get_latest_image_excluding_prefixes(image_type, ["https://placehold.co/"])
    elif image_type == "rainfall":
        image = get_latest_image_by_image_time(image_type)
    else:
        image = get_latest_image(image_type)

    if image is None:
        return jsonify({"error": "Image type not found."}), 404
    return jsonify(serialize_image(image))


@images_bp.get("/history")
def image_history():
    image_type = request.args.get("type", "").strip()
    if not image_type:
        return jsonify({"error": "Query parameter 'type' is required."}), 400

    image_date = request.args.get("date", "").strip()
    if image_date:
        try:
            date.fromisoformat(image_date)
        except ValueError:
            return jsonify({"error": "Query parameter 'date' must use YYYY-MM-DD."}), 400
        return jsonify([serialize_image(image) for image in get_image_history_by_date(image_type, image_date)])

    limit = request.args.get("limit", default=20, type=int)
    return jsonify([serialize_image(image) for image in get_image_history(image_type, limit)])


@images_bp.get("/daily")
def daily_images():
    image_type = request.args.get("type", "").strip()
    if image_type != "rainfall":
        return jsonify({"error": "Daily representatives are only supported for rainfall."}), 400

    image_date = request.args.get("date", "").strip()
    if image_date:
        try:
            target_date = date.fromisoformat(image_date)
        except ValueError:
            return jsonify({"error": "Query parameter 'date' must use YYYY-MM-DD."}), 400
    else:
        target_date = datetime.now(timezone.utc).date()

    representatives = []
    for slot in rainfall_daily_representative_slots(target_date):
        image_time = slot["image_time"].strftime("%Y-%m-%d %H:%M")
        image = get_image_by_image_time("rainfall", image_time)
        if image is None:
            continue
        serialized = serialize_image(image)
        serialized["label"] = slot["label"]
        serialized["represented_date"] = slot["represented_date"]
        representatives.append(serialized)

    return jsonify(representatives)


@images_bp.post("/backfill")
def backfill_images():
    image_type = request.args.get("type", "").strip()
    if image_type != "rainfall":
        return jsonify({"error": "Backfill is only supported for rainfall."}), 400

    range_name = request.args.get("range", "today").strip() or "today"
    image_date = request.args.get("date", "").strip()
    parsed_date = None
    if image_date:
        try:
            parsed_date = date.fromisoformat(image_date)
        except ValueError:
            return jsonify({"error": "Query parameter 'date' must use YYYY-MM-DD."}), 400

    if range_name != "today" and parsed_date is None:
        return jsonify({"error": "Only range=today or date=YYYY-MM-DD is supported."}), 400

    try:
        summary = backfill_rainfall_images(range_name=range_name, image_date=parsed_date)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(summary)
