from flask import Blueprint, jsonify, request

from ..jobs import fetch_radar_image, fetch_satellite_image
from ..models.image_repository import get_image_history, get_latest_image, get_latest_image_excluding_prefixes


images_bp = Blueprint("images", __name__)


@images_bp.get("/latest")
def latest_image():
    image_type = request.args.get("type", "").strip()
    if not image_type:
        return jsonify({"error": "Query parameter 'type' is required."}), 400

    if image_type == "satellite":
        fetch_satellite_image()
    elif image_type == "radar":
        fetch_radar_image()

    if image_type == "radar":
        image = get_latest_image_excluding_prefixes(image_type, ["https://placehold.co/"])
    else:
        image = get_latest_image(image_type)

    if image is None:
        return jsonify({"error": "Image type not found."}), 404
    return jsonify(image)


@images_bp.get("/history")
def image_history():
    image_type = request.args.get("type", "").strip()
    if not image_type:
        return jsonify({"error": "Query parameter 'type' is required."}), 400

    limit = request.args.get("limit", default=20, type=int)
    return jsonify(get_image_history(image_type, limit))
