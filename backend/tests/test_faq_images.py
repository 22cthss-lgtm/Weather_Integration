import io
import unittest
from pathlib import Path
from unittest.mock import patch

from flask import Flask

from src.api.faqs import faq_bp


IMAGE_SAMPLES = {
    "jpg": (b"\xff\xd8\xff\xe0" + b"JFIF\x00" + b"jpeg-data", "image/jpeg"),
    "png": (b"\x89PNG\r\n\x1a\n" + b"png-data", "image/png"),
    "webp": (b"RIFF\x10\x00\x00\x00WEBPVP8 " + b"webp-data", "image/webp"),
    "gif": (b"GIF89a" + b"gif-data", "image/gif"),
}


class FaqImageApiTests(unittest.TestCase):
    def setUp(self):
        self.upload_dir = Path(__file__).parent
        self.existing_files = set(self.upload_dir.glob("*.jpg")) | set(
            self.upload_dir.glob("*.png")
        ) | set(self.upload_dir.glob("*.webp")) | set(self.upload_dir.glob("*.gif"))
        self.upload_patcher = patch(
            "src.api.faqs.FAQ_UPLOAD_DIR", self.upload_dir, create=True
        )
        self.upload_patcher.start()

        app = Flask(__name__)
        app.register_blueprint(faq_bp, url_prefix="/api/faqs")
        self.client = app.test_client()

    def tearDown(self):
        self.upload_patcher.stop()
        current_files = set(self.upload_dir.glob("*.jpg")) | set(
            self.upload_dir.glob("*.png")
        ) | set(self.upload_dir.glob("*.webp")) | set(self.upload_dir.glob("*.gif"))
        for path in current_files - self.existing_files:
            path.unlink(missing_ok=True)

    def upload(self, content, filename, mime_type):
        return self.client.post(
            "/api/faqs/images",
            data={"image": (io.BytesIO(content), filename, mime_type)},
            content_type="multipart/form-data",
        )

    def test_uploads_supported_images_and_serves_the_saved_bytes(self):
        for extension, (content, mime_type) in IMAGE_SAMPLES.items():
            with self.subTest(extension=extension):
                response = self.upload(content, f"weather.{extension}", mime_type)
                self.assertEqual(response.status_code, 201)
                self.assertRegex(
                    response.json["url"],
                    rf"/api/faqs/images/[0-9a-f-]{{36}}\.{extension}$",
                )
                served = self.client.get(response.json["url"])
                self.assertEqual(served.status_code, 200)
                self.assertEqual(served.data, content)
                self.assertEqual(served.content_type, mime_type)
                served.close()

    def test_jpeg_extension_is_canonicalized_to_jpg(self):
        content, mime_type = IMAGE_SAMPLES["jpg"]
        response = self.upload(content, "photo.jpeg", mime_type)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json["url"].endswith(".jpg"))

    def test_rejects_missing_or_empty_image(self):
        missing = self.client.post("/api/faqs/images", data={})
        empty = self.upload(b"", "empty.png", "image/png")
        self.assertEqual(missing.status_code, 400)
        self.assertEqual(empty.status_code, 400)
        self.assertIn("error", missing.json)
        self.assertIn("error", empty.json)

    def test_rejects_image_larger_than_ten_megabytes(self):
        response = self.upload(
            IMAGE_SAMPLES["png"][0] + b"x" * (10 * 1024 * 1024),
            "large.png",
            "image/png",
        )
        self.assertEqual(response.status_code, 413)
        self.assertIn("10 MB", response.json["error"])

    def test_rejects_non_image_extension_and_mime(self):
        response = self.upload(b"plain text", "notes.txt", "text/plain")
        self.assertEqual(response.status_code, 400)
        self.assertIn("image", response.json["error"].lower())

    def test_rejects_extension_mime_and_signature_mismatches(self):
        png, _ = IMAGE_SAMPLES["png"]
        jpeg, _ = IMAGE_SAMPLES["jpg"]
        cases = [
            (png, "wrong.jpg", "image/png"),
            (jpeg, "wrong.png", "image/png"),
            (b"not-a-png", "fake.png", "image/png"),
        ]
        for content, filename, mime_type in cases:
            with self.subTest(filename=filename, mime_type=mime_type):
                response = self.upload(content, filename, mime_type)
                self.assertEqual(response.status_code, 400)

    def test_original_path_traversal_name_is_never_used(self):
        content, mime_type = IMAGE_SAMPLES["png"]
        response = self.upload(content, "../../outside.png", mime_type)
        self.assertEqual(response.status_code, 201)
        self.assertNotIn("outside", response.json["url"])
        self.assertRegex(response.json["url"], r"[0-9a-f-]{36}\.png$")

    def test_serving_rejects_non_uuid_and_disallowed_extensions(self):
        for filename in ["test_faq_images.py", "../app.py", "not-a-uuid.png", "0" * 36 + ".txt"]:
            with self.subTest(filename=filename):
                response = self.client.get(f"/api/faqs/images/{filename}")
                self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
