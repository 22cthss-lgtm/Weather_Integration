import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.db import get_connection, init_db
from src.models.image_repository import get_latest_image, insert_image


class ImageRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "weather.db"

        self.db_path_patcher = patch("src.db.DATABASE_PATH", self.database_path)
        self.db_path_patcher.start()
        init_db()

    def tearDown(self):
        self.db_path_patcher.stop()
        self.temp_dir.cleanup()

    def count_images(self, image_type):
        with get_connection() as conn:
            return conn.execute(
                "SELECT COUNT(*) AS count FROM images WHERE image_type = ?",
                (image_type,),
            ).fetchone()["count"]

    def test_insert_image_skips_exact_duplicate_of_latest_record(self):
        payload = {
            "image_type": "satellite",
            "source": "CWA",
            "title": "CWA Color Satellite Cloud 2026-05-12 16:00",
            "image_url": "https://www.cwa.gov.tw/Data/satellite/example.jpg",
            "source_url": "https://www.cwa.gov.tw/V8/C/W/OBS_Sat.html",
        }

        insert_image(**payload, fetched_at="2026-05-12T08:00:00+00:00")
        insert_image(**payload, fetched_at="2026-05-12T08:05:00+00:00")

        latest_image = get_latest_image("satellite")

        self.assertEqual(self.count_images("satellite"), 1)
        self.assertEqual(latest_image["fetched_at"], "2026-05-12T08:00:00+00:00")

    def test_insert_image_allows_changed_title_or_image_url(self):
        base_payload = {
            "image_type": "radar",
            "source": "CWA",
            "title": "CWA Radar Echo 2026-05-12 16:00",
            "image_url": "https://www.cwa.gov.tw/Data/radar/CV1_3600_202605121600.png",
            "source_url": "https://www.cwa.gov.tw/V8/C/W/OBS_Radar.html",
        }

        insert_image(**base_payload, fetched_at="2026-05-12T08:00:00+00:00")
        insert_image(
            **{
                **base_payload,
                "title": "CWA Radar Echo 2026-05-12 16:10",
                "image_url": "https://www.cwa.gov.tw/Data/radar/CV1_3600_202605121610.png",
            },
            fetched_at="2026-05-12T08:10:00+00:00",
        )

        latest_image = get_latest_image("radar")

        self.assertEqual(self.count_images("radar"), 2)
        self.assertEqual(latest_image["title"], "CWA Radar Echo 2026-05-12 16:10")


if __name__ == "__main__":
    unittest.main()
