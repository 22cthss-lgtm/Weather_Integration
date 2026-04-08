import sqlite3

from flask import Blueprint, jsonify, request

from ..models.doc_repository import create_doc, delete_doc, get_doc, list_docs, update_doc


docs_bp = Blueprint("docs", __name__)


@docs_bp.get("")
def docs_list():
    return jsonify(list_docs())


@docs_bp.get("/<int:doc_id>")
def docs_detail(doc_id: int):
    doc = get_doc(doc_id)
    if doc is None:
        return jsonify({"error": "Document not found."}), 404
    return jsonify(doc)


@docs_bp.post("")
def docs_create():
    payload = request.get_json(silent=True) or {}
    title = payload.get("title", "").strip()
    slug = payload.get("slug", "").strip()
    content = payload.get("content", "").strip()

    if not title or not slug:
        return jsonify({"error": "Both 'title' and 'slug' are required."}), 400

    try:
        doc = create_doc(title=title, slug=slug, content=content)
    except sqlite3.IntegrityError:
        return jsonify({"error": "Slug must be unique."}), 409
    return jsonify(doc), 201


@docs_bp.put("/<int:doc_id>")
def docs_update(doc_id: int):
    payload = request.get_json(silent=True) or {}
    title = payload.get("title", "").strip()
    slug = payload.get("slug", "").strip()
    content = payload.get("content", "").strip()

    if not title or not slug:
        return jsonify({"error": "Both 'title' and 'slug' are required."}), 400

    try:
        doc = update_doc(doc_id=doc_id, title=title, slug=slug, content=content)
    except sqlite3.IntegrityError:
        return jsonify({"error": "Slug must be unique."}), 409

    if doc is None:
        return jsonify({"error": "Document not found."}), 404
    return jsonify(doc)


@docs_bp.delete("/<int:doc_id>")
def docs_delete(doc_id: int):
    deleted = delete_doc(doc_id)
    if not deleted:
        return jsonify({"error": "Document not found."}), 404
    return jsonify({"status": "deleted"})
