import re
from datetime import datetime

from flask import Blueprint, jsonify, request

from ..jobs import (
    fetch_850hpa_image,
    fetch_radar_image,
    fetch_rainfall_image,
    fetch_satellite_image,
    fetch_sst_image,
    fetch_temperature_image,
    fetch_weather_chart_image,
)
from ..models.image_repository import get_image_history, get_latest_image, get_latest_image_excluding_prefixes


images_bp = Blueprint("images", __name__)
image_time_regex = re.compile(r"(?P<image_time>\d{4}-\d{2}-\d{2} \d{2}:\d{2})$")
image_types_with_embedded_time = {"temperature", "rainfall", "850hpa", "weather_chart"}


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
    elif image_type == "sst":
        fetch_sst_image()
    elif image_type == "850hpa":
        fetch_850hpa_image()

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
