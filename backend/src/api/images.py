import re
from datetime import datetime

from flask import Blueprint, jsonify, request

from ..jobs import (
    fetch_cimss_steering_flow_images,
    fetch_cimss_wind_analysis_images,
    fetch_850hpa_image,
    fetch_radar_image,
    fetch_rainfall_image,
    fetch_seaice_antarctic_images,
    fetch_seaice_images,
    fetch_satellite_image,
    fetch_sst_image,
    fetch_temperature_image,
    fetch_tchp_image,
    fetch_weather_chart_image,
)
from ..models.image_repository import get_image_history, get_latest_image, get_latest_image_excluding_prefixes


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
    "seaice_extent",
    "seaice_concentration",
    "seaice_timeseries",
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


def serialize_image(image: dict) -> dict:
    serialized = dict(image)
    if serialized.get("image_type") in image_types_with_embedded_time:
        match = image_time_regex.search(serialized.get("title", ""))
        if match:
            serialized["image_time"] = match.group("image_time")
        elif serialized.get("image_type") == "weather_chart" and serialized.get("fetched_at"):
            fetched_at = datetime.fromisoformat(serialized["fetched_at"])
            serialized["image_time"] = fetched_at.strftime("%Y-%m-%d %H:%M")
    return serialized


def serialize_seaice_payload() -> dict | None:
    return serialize_grouped_payload(
        aggregate_type="seaice",
        source="NSIDC",
        image_types=["seaice_extent", "seaice_concentration", "seaice_timeseries"],
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
    elif image_type == "seaice":
        fetch_seaice_images()
    elif image_type == "seaice_antarctic":
        fetch_seaice_antarctic_images()
    elif image_type == "cimss_wind_analysis":
        fetch_cimss_wind_analysis_images()
    elif image_type == "cimss_steering_flow":
        fetch_cimss_steering_flow_images()

    if image_type == "seaice":
        image = serialize_seaice_payload()
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

    limit = request.args.get("limit", default=20, type=int)
    return jsonify(get_image_history(image_type, limit))
