import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from flask import Flask

from src.api.faqs import faq_bp
from src.db import init_db
from src.models.faq_repository import create_faq, list_categories
from src.seed import seed_faqs


class FaqApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "weather.db"

        self.db_path_patcher = patch("src.db.DATABASE_PATH", self.database_path)
        self.db_path_patcher.start()
        init_db()
        seed_faqs()

        app = Flask(__name__)
        app.register_blueprint(faq_bp, url_prefix="/api/faqs")
        self.client = app.test_client()

    def tearDown(self):
        self.db_path_patcher.stop()
        self.temp_dir.cleanup()

    def test_list_faqs_returns_seeded_records_sorted_by_pinned_then_updated(self):
        response = self.client.get("/api/faqs")

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.json), 2)
        self.assertTrue(response.json[0]["is_pinned"])
        self.assertIn("summary", response.json[0])
        self.assertIn("updated_at", response.json[0])
        self.assertIsInstance(response.json[0]["tags"], list)

    def test_list_faqs_supports_category_filter(self):
        response = self.client.get("/api/faqs?category=觀測資料")

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.json), 1)
        self.assertTrue(all(item["category"] == "觀測資料" for item in response.json))

    def test_list_faqs_supports_keyword_search(self):
        response = self.client.get("/api/faqs?q=衛星")

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.json), 1)
        self.assertTrue(any("衛星" in item["title"] or "衛星" in item["summary"] for item in response.json))

    def test_get_faq_detail_returns_full_markdown_content(self):
        response = self.client.get("/api/faqs/1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["id"], 1)
        self.assertIn("#", response.json["content"])

    def test_get_faq_detail_returns_404_for_missing_record(self):
        response = self.client.get("/api/faqs/999")

        self.assertEqual(response.status_code, 404)

    def test_create_faq_creates_record_and_upserts_new_category(self):
        response = self.client.post(
            "/api/faqs",
            json={
                "category": "資料來源",
                "title": "FAQ 測試條目",
                "summary": "建立 FAQ 測試",
                "content": "# 測試內容",
                "tags": ["測試", "API"],
                "is_pinned": True,
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["category"], "資料來源")
        self.assertEqual(response.json["tags"], ["測試", "API"])
        self.assertTrue(response.json["is_pinned"])
        self.assertIn("資料來源", [item["name"] for item in list_categories()])

    def test_update_faq_updates_existing_record(self):
        response = self.client.put(
            "/api/faqs/1",
            json={
                "category": "觀測資料",
                "title": "更新後 FAQ",
                "summary": "更新後摘要",
                "content": "## 更新後內容",
                "tags": ["更新"],
                "is_pinned": False,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["title"], "更新後 FAQ")
        self.assertEqual(response.json["category"], "觀測資料")
        self.assertEqual(response.json["tags"], ["更新"])
        self.assertFalse(response.json["is_pinned"])

    def test_delete_faq_removes_record(self):
        faq = create_faq(
            category="系統",
            title="待刪除 FAQ",
            summary="待刪除摘要",
            content="待刪除內容",
            tags=["刪除"],
            is_pinned=False,
        )

        delete_response = self.client.delete(f"/api/faqs/{faq['id']}")
        detail_response = self.client.get(f"/api/faqs/{faq['id']}")

        self.assertEqual(delete_response.status_code, 200)
        self.assertEqual(detail_response.status_code, 404)

    def test_categories_exclude_categories_without_faqs(self):
        faq = create_faq(
            category="Test123",
            title="Temporary FAQ",
            summary="Temporary summary",
            content="Temporary content",
            tags=[],
            is_pinned=False,
        )

        create_response = self.client.get("/api/faqs/categories")
        self.assertIn("Test123", [item["name"] for item in create_response.json])

        self.client.delete(f"/api/faqs/{faq['id']}")
        response = self.client.get("/api/faqs/categories")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Test123", [item["name"] for item in response.json])

    def test_list_categories_returns_seeded_and_sorted_categories(self):
        response = self.client.get("/api/faqs/categories")

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.json), 2)
        self.assertEqual(response.json[0]["name"], "系統使用")


if __name__ == "__main__":
    unittest.main()
