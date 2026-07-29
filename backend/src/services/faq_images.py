from pathlib import Path
from uuid import uuid4


MAX_FAQ_IMAGE_BYTES = 10 * 1024 * 1024
EXTENSION_TO_FORMAT = {
    ".jpg": "jpg",
    ".jpeg": "jpg",
    ".png": "png",
    ".webp": "webp",
    ".gif": "gif",
}
FORMAT_TO_MIME = {
    "jpg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "gif": "image/gif",
}


class FaqImageError(ValueError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _detect_image_format(content: bytes) -> str | None:
    if content.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if content.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "webp"
    return None


def save_faq_image(upload, upload_dir: Path) -> tuple[str, str]:
    original_name = str(upload.filename or "")
    extension = Path(original_name).suffix.lower()
    expected_format = EXTENSION_TO_FORMAT.get(extension)
    if expected_format is None:
        raise FaqImageError("Only JPG, JPEG, PNG, WEBP, and GIF images are allowed.")

    declared_mime = (upload.mimetype or "").lower()
    if declared_mime != FORMAT_TO_MIME[expected_format]:
        raise FaqImageError("The image MIME type does not match its file extension.")

    content = upload.stream.read(MAX_FAQ_IMAGE_BYTES + 1)
    if not content:
        raise FaqImageError("The uploaded image is empty.")
    if len(content) > MAX_FAQ_IMAGE_BYTES:
        raise FaqImageError("FAQ images must be 10 MB or smaller.", status_code=413)

    detected_format = _detect_image_format(content)
    if detected_format != expected_format:
        raise FaqImageError("The uploaded file content does not match its image type.")

    filename = f"{uuid4()}.{expected_format}"
    upload_dir.mkdir(parents=True, exist_ok=True)
    (upload_dir / filename).write_bytes(content)
    return filename, FORMAT_TO_MIME[expected_format]
