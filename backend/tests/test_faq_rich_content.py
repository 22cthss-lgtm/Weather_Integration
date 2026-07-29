import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from flask import Flask

from src.api.faqs import faq_bp
from src.db import init_db


class FaqRichContentTests(unittest.TestCase):
    def setUp(self):
        self.database_path = Path(__file__).parent / f"faq-rich-{uuid4().hex}.db"
        self.db_path_patcher = patch("src.db.DATABASE_PATH", self.database_path)
        self.db_path_patcher.start()
        init_db()

        app = Flask(__name__)
        app.register_blueprint(faq_bp, url_prefix="/api/faqs")
        self.client = app.test_client()

    def tearDown(self):
        self.db_path_patcher.stop()
        self.database_path.unlink(missing_ok=True)

    def payload(self, content):
        return {
            "category": "Security",
            "title": "Rich content",
            "summary": "Sanitizer behavior",
            "content": content,
            "tags": ["html"],
            "is_pinned": False,
        }

    def test_create_retains_supported_tiptap_html(self):
        content = (
            '<h2 style="text-align: center">Heading</h2>'
            '<p><strong>Bold</strong> <em>italic</em> <u>underline</u> '
            '<s>strike</s> <span style="font-size: 20px; color: #123456; '
            'background-color: #ffeeaa">color</span></p>'
            '<ul><li><p>Item</p></li></ul>'
            '<a href="https://example.com" target="_blank" '
            'rel="noopener noreferrer">link</a>'
            '<img src="http://localhost:5174/api/faqs/images/'
            '00000000-0000-4000-8000-000000000000.png" alt="FAQ image">'
        )

        response = self.client.post("/api/faqs", json=self.payload(content))

        self.assertEqual(response.status_code, 201)
        self.assertIn('<h2 style="text-align: center;">', response.json["content"])
        self.assertIn("font-size: 20px", response.json["content"])
        self.assertIn("background-color: #ffeeaa", response.json["content"])
        self.assertIn('rel="noopener noreferrer"', response.json["content"])
        self.assertIn("<img", response.json["content"])

    def test_create_removes_scripts_events_unsafe_urls_and_unsupported_styles(self):
        content = (
            '<p onclick="alert(1)" style="position: fixed; color: red">Safe</p>'
            '<script>alert(1)</script>'
            '<a href="javascript:alert(1)" onmouseover="alert(2)">bad</a>'
            '<img src="javascript:alert(3)" onerror="alert(4)">'
            '<img src="mailto:image@example.com">'
        )

        response = self.client.post("/api/faqs", json=self.payload(content))

        self.assertEqual(response.status_code, 201)
        saved = response.json["content"]
        self.assertNotIn("<script", saved)
        self.assertNotIn("alert(1)", saved)
        self.assertNotIn("onclick", saved)
        self.assertNotIn("onmouseover", saved)
        self.assertNotIn("onerror", saved)
        self.assertNotIn("javascript:", saved)
        self.assertNotIn("mailto:image", saved)
        self.assertNotIn("position", saved)
        self.assertIn("color: red", saved)

    def test_create_rejects_visually_empty_html(self):
        for content in ["<p></p>", "<p><br></p>", "<p><span> &nbsp; </span></p>"]:
            with self.subTest(content=content):
                response = self.client.post("/api/faqs", json=self.payload(content))
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json["error"], "'content' is required.")

    def test_create_allows_image_only_content(self):
        response = self.client.post(
            "/api/faqs",
            json=self.payload(
                '<p><img src="http://localhost:5174/api/faqs/images/'
                '00000000-0000-4000-8000-000000000000.png"></p>'
            ),
        )

        self.assertEqual(response.status_code, 201)


if __name__ == "__main__":
    unittest.main()
