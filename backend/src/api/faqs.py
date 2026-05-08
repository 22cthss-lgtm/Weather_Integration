from flask import Blueprint, jsonify, request

from ..models.faq_repository import create_faq, delete_faq, get_faq, list_categories, list_faqs, update_faq


faq_bp = Blueprint("faqs", __name__)


def _parse_tags(raw_tags) -> list[str]:
    if raw_tags is None:
        return []
    if isinstance(raw_tags, list):
        return [str(tag).strip() for tag in raw_tags if str(tag).strip()]
    if isinstance(raw_tags, str):
        return [tag.strip() for tag in raw_tags.split(",") if tag.strip()]
    return []


def _validate_payload(payload: dict) -> str | None:
    for field in ["category", "title", "summary", "content"]:
        if not str(payload.get(field, "")).strip():
            return f"'{field}' is required."
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


@faq_bp.get("/<int:faq_id>")
def faq_detail(faq_id: int):
    faq = get_faq(faq_id)
    if faq is None:
        return jsonify({"error": "FAQ not found."}), 404
    return jsonify(faq)


@faq_bp.post("")
def faq_create():
    payload = request.get_json(silent=True) or {}
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
