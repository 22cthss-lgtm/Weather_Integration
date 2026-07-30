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

    def test_create_and_read_retain_safe_table_structure(self):
        content = (
            '<table><thead><tr><th colspan="2" rowspan="1">Heading</th></tr></thead>'
            '<tbody><tr><td rowspan="2">A</td><td>B</td></tr>'
            '<tr><td colspan="1">C</td></tr></tbody></table>'
        )

        create_response = self.client.post("/api/faqs", json=self.payload(content))

        self.assertEqual(create_response.status_code, 201)
        faq_id = create_response.json["id"]
        detail_response = self.client.get(f"/api/faqs/{faq_id}")
        self.assertEqual(detail_response.status_code, 200)
        saved = detail_response.json["content"]
        self.assertIn("<table>", saved)
        self.assertIn("<thead>", saved)
        self.assertIn("<tbody>", saved)
        self.assertIn('<th colspan="2" rowspan="1">Heading</th>', saved)
        self.assertIn('<td rowspan="2">A</td>', saved)

    def test_create_removes_dangerous_table_content_and_attributes(self):
        content = (
            '<table onclick="alert(1)" style="position: fixed"><tbody><tr>'
            '<td colspan="2" rowspan="2" onerror="alert(2)" data-secret="x">Safe'
            '<iframe src="https://example.com">hidden</iframe>'
            '<script>alert(3)</script></td></tr></tbody></table>'
        )

        response = self.client.post("/api/faqs", json=self.payload(content))

        self.assertEqual(response.status_code, 201)
        saved = response.json["content"]
        self.assertIn('<td colspan="2" rowspan="2">Safehidden</td>', saved)
        self.assertNotIn("onclick", saved)
        self.assertNotIn("onerror", saved)
        self.assertNotIn("data-secret", saved)
        self.assertNotIn("position", saved)
        self.assertNotIn("iframe", saved)
        self.assertNotIn("script", saved)
        self.assertNotIn("alert", saved)

    def test_create_and_update_retain_controlled_table_sizing_and_alignment(self):
        content = (
            '<table data-table-width="75" style="width: 75%; position: fixed">'
            '<colgroup><col style="width: 120px; color: red">'
            '<col style="min-width: 80px"></colgroup><tbody><tr>'
            '<td data-vertical-align="middle">A</td>'
            '<td data-vertical-align="sideways" data-secret="x">B</td>'
            '</tr></tbody></table>'
        )

        create_response = self.client.post("/api/faqs", json=self.payload(content))
        self.assertEqual(create_response.status_code, 201)
        saved = create_response.json["content"]
        self.assertIn('data-table-width="75"', saved)
        self.assertIn("width: 75%", saved)
        self.assertIn("<colgroup>", saved)
        self.assertIn("width: 120px", saved)
        self.assertIn("min-width: 80px", saved)
        self.assertIn('data-vertical-align="middle"', saved)
        self.assertNotIn("position", saved)
        self.assertNotIn("color", saved)
        self.assertNotIn("sideways", saved)
        self.assertNotIn("data-secret", saved)

        updated = content.replace('data-table-width="75"', 'data-table-width="50"')
        update_response = self.client.put(
            f'/api/faqs/{create_response.json["id"]}', json=self.payload(updated)
        )
        self.assertEqual(update_response.status_code, 200)
        detail_response = self.client.get(f'/api/faqs/{create_response.json["id"]}')
        self.assertIn('data-table-width="50"', detail_response.json["content"])

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
