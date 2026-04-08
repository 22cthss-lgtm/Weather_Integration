from .models.doc_repository import create_doc, list_docs


def seed_docs() -> None:
    if list_docs():
        return

    create_doc(
        title="Platform Overview",
        slug="platform-overview",
        content=(
            "# Platform Overview\n\n"
            "This demo site aggregates weather, ocean, AQI, and reservoir imagery.\n\n"
            "## Included APIs\n\n"
            "- `/api/images/latest?type=...`\n"
            "- `/api/images/history?type=...`\n"
            "- `/api/docs`\n"
        ),
    )
