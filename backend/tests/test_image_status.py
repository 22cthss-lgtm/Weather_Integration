import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from src.db import init_db
from src.models.image_repository import insert_image


class ImageStatusTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "weather.db"

        self.db_path_patcher = patch("src.db.DATABASE_PATH", self.database_path)
        self.db_path_patcher.start()
        init_db()

    def tearDown(self):
        self.db_path_patcher.stop()
        self.temp_dir.cleanup()

    def test_status_summary_reports_no_data_for_known_type(self):
        from src.services.status_service import build_image_status_summaries

        payload = build_image_status_summaries(
            image_types=["satellite"],
            now=datetime(2026, 5, 20, 12, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(payload["items"][0]["image_type"], "satellite")
        self.assertEqual(payload["items"][0]["total_records"], 0)
        self.assertEqual(payload["items"][0]["freshness_status"], "No Data")
        self.assertIn("No records found", payload["items"][0]["note"])

    def test_status_summary_counts_recent_records_and_parses_data_time(self):
        from src.services.status_service import build_image_status_summaries

        insert_image(
            image_type="radar",
            source="CWA",
            title="CWA Radar Echo 2026-05-20 19:50",
            image_url="https://example.test/radar-1950.png",
            source_url="https://example.test/radar",
            fetched_at="2026-05-20T11:50:00+00:00",
        )

        payload = build_image_status_summaries(
            image_types=["radar"],
            now=datetime(2026, 5, 20, 12, 0, tzinfo=timezone.utc),
        )
        status = payload["items"][0]

        self.assertEqual(status["total_records"], 1)
        self.assertEqual(status["added_today"], 1)
        self.assertEqual(status["added_last_24h"], 1)
        self.assertEqual(status["latest_data_time"], "2026-05-20 19:50")
        self.assertEqual(status["freshness_status"], "Fresh")

    def test_status_summary_detects_previous_url_and_possible_duplicates(self):
        from src.services.status_service import build_image_status_summaries

        base_payload = {
            "image_type": "satellite",
            "source": "CWA",
            "source_url": "https://example.test/satellite",
        }
        insert_image(
            **base_payload,
            title="CWA Satellite 2026-05-20 19:30",
            image_url="https://example.test/satellite-1930.jpg",
            fetched_at="2026-05-20T11:30:00+00:00",
        )
        insert_image(
            **base_payload,
            title="CWA Satellite updated title",
            image_url="https://example.test/satellite-1930.jpg",
            fetched_at="2026-05-20T11:40:00+00:00",
        )

        payload = build_image_status_summaries(
            image_types=["satellite"],
            now=datetime(2026, 5, 20, 12, 0, tzinfo=timezone.utc),
        )
        status = payload["items"][0]

        self.assertEqual(status["previous_image_url"], "https://example.test/satellite-1930.jpg")
        self.assertTrue(status["latest_url_same_as_previous"])
        self.assertEqual(status["possible_duplicate_count"], 1)
        self.assertIn("Latest URL matches previous record", status["note"])

    def test_status_summary_uses_unknown_when_no_explicit_ttl_exists(self):
        from src.services.status_service import build_image_status_summaries

        insert_image(
            image_type="test_no_ttl",
            source="TEST",
            title="Test Image Without TTL 2026-05-20",
            image_url="https://example.test/no-ttl.png",
            source_url="https://example.test/no-ttl",
            fetched_at="2026-05-20T00:00:00+00:00",
        )

        payload = build_image_status_summaries(
            image_types=["test_no_ttl"],
            now=datetime(2026, 5, 20, 12, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(payload["items"][0]["freshness_status"], "Unknown")
        self.assertIn("No explicit TTL configured", payload["items"][0]["note"])


if __name__ == "__main__":
    unittest.main()
