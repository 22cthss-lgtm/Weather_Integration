import re

from flask import Blueprint, abort, jsonify, request, send_from_directory, url_for

from ..config import FAQ_UPLOAD_DIR
from ..models.faq_repository import create_faq, delete_faq, get_faq, list_categories, list_faqs, update_faq
from ..services.faq_content import is_faq_content_empty, sanitize_faq_content
from ..services.faq_images import FaqImageError, save_faq_image


faq_bp = Blueprint("faqs", __name__)
FAQ_IMAGE_FILENAME_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\.(?:jpg|png|webp|gif)$"
)


def _parse_tags(raw_tags) -> list[str]:
    if raw_tags is None:
        return []
    if isinstance(raw_tags, list):
        return [str(tag).strip() for tag in raw_tags if str(tag).strip()]
    if isinstance(raw_tags, str):
        return [tag.strip() for tag in raw_tags.split(",") if tag.strip()]
    return []


def _validate_payload(payload: dict) -> str | None:
    for field in ["category", "title", "summary"]:
        if not str(payload.get(field, "")).strip():
            return f"'{field}' is required."
    if is_faq_content_empty(str(payload.get("content", ""))):
        return "'content' is required."
    return None


@faq_bp.get("")
def faq_list():
    category = request.args.get("category", "").strip() or None
    query = request.args.get("q", "").strip() or None
    pinned_arg = request.args.get("pinned")
    pinned = None
    if pinned_arg is not None:
        pinned = pinned_arg.strip().lower() == "true"
    return jsonify(list_faqs(category=category, query=query, pinned=pinned))


@faq_bp.get("/categories")
def faq_categories():
    return jsonify(list_categories())


@faq_bp.post("/images")
def faq_image_upload():
    upload = request.files.get("image")
    if upload is None:
        return jsonify({"error": "An image file is required."}), 400

    try:
        filename, _mime_type = save_faq_image(upload, FAQ_UPLOAD_DIR)
    except FaqImageError as error:
        return jsonify({"error": str(error)}), error.status_code

    return jsonify({"url": url_for("faqs.faq_image", filename=filename, _external=True)}), 201


@faq_bp.get("/images/<path:filename>")
def faq_image(filename: str):
    if not FAQ_IMAGE_FILENAME_PATTERN.fullmatch(filename):
        abort(404)
    return send_from_directory(FAQ_UPLOAD_DIR, filename)


@faq_bp.get("/<int:faq_id>")
def faq_detail(faq_id: int):
    faq = get_faq(faq_id)
    if faq is None:
        return jsonify({"error": "FAQ not found."}), 404
    return jsonify(faq)


@faq_bp.post("")
def faq_create():
    payload = request.get_json(silent=True) or {}
    payload["content"] = sanitize_faq_content(str(payload.get("content", "")))
    validation_error = _validate_payload(payload)
    if validation_error:
        return jsonify({"error": validation_error}), 400

    faq = create_faq(
        category=str(payload.get("category", "")).strip(),
        title=str(payload.get("title", "")).strip(),
        summary=str(payload.get("summary", "")).strip(),
        content=str(payload.get("content", "")).strip(),
        tags=_parse_tags(payload.get("tags")),
        is_pinned=bool(payload.get("is_pinned", False)),
    )
    return jsonify(faq), 201


@faq_bp.put("/<int:faq_id>")
def faq_update(faq_id: int):
    payload = request.get_json(silent=True) or {}
    payload["content"] = sanitize_faq_content(str(payload.get("content", "")))
    validation_error = _validate_payload(payload)
    if validation_error:
        return jsonify({"error": validation_error}), 400

    faq = update_faq(
        faq_id=faq_id,
        category=str(payload.get("category", "")).strip(),
        title=str(payload.get("title", "")).strip(),
        summary=str(payload.get("summary", "")).strip(),
        content=str(payload.get("content", "")).strip(),
        tags=_parse_tags(payload.get("tags")),
        is_pinned=bool(payload.get("is_pinned", False)),
    )
    if faq is None:
        return jsonify({"error": "FAQ not found."}), 404
    return jsonify(faq)


@faq_bp.delete("/<int:faq_id>")
def faq_delete(faq_id: int):
    deleted = delete_faq(faq_id)
    if not deleted:
        return jsonify({"error": "FAQ not found."}), 404
    return jsonify({"status": "deleted"})
