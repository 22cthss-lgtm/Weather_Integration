import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from flask import Flask

from src.api.images import images_bp
from src.db import init_db
from src.models.image_repository import insert_image


class LatestSatelliteAndRadarApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "weather.db"

        self.db_path_patcher = patch("src.db.DATABASE_PATH", self.database_path)
        self.db_path_patcher.start()
        init_db()

        app = Flask(__name__)
        app.register_blueprint(images_bp, url_prefix="/api/images")
        self.client = app.test_client()

    def tearDown(self):
        self.db_path_patcher.stop()
        self.temp_dir.cleanup()

    def test_latest_satellite_returns_image_time_from_title(self):
        insert_image(
            image_type="satellite",
            source="CWA",
            title="CWA Color Satellite Cloud 2026-04-15 00:00",
            image_url="https://www.cwa.gov.tw/Data/satellite/LCC_IR1_CR_2750/LCC_IR1_CR_2750-2026-04-15-00-00.jpg",
            source_url="https://www.cwa.gov.tw/V8/C/W/OBS_Sat.html",
            fetched_at="2026-04-15T00:35:00+08:00",
        )

        with patch("src.api.images.fetch_satellite_image") as mock_fetch:
            response = self.client.get("/api/images/latest?type=satellite")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["image_time"], "2026-04-15 00:00")
        mock_fetch.assert_called_once_with()

    def test_latest_satellite_skips_fetch_when_latest_record_is_fresh(self):
        insert_image(
            image_type="satellite",
            source="CWA",
            title="CWA Color Satellite Cloud 2026-05-12 16:00",
            image_url="https://www.cwa.gov.tw/Data/satellite/LCC_IR1_CR_2750/LCC_IR1_CR_2750-2026-05-12-16-00.jpg",
            source_url="https://www.cwa.gov.tw/V8/C/W/OBS_Sat.html",
            fetched_at=datetime.now(timezone.utc).isoformat(),
        )

        with patch("src.api.images.fetch_satellite_image") as mock_fetch:
            response = self.client.get("/api/images/latest?type=satellite")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["image_time"], "2026-05-12 16:00")
        mock_fetch.assert_not_called()

    def test_latest_satellite_fetches_when_latest_record_exceeds_ten_minute_ttl(self):
        insert_image(
            image_type="satellite",
            source="CWA",
            title="CWA Color Satellite Cloud 2026-05-12 16:00",
            image_url="https://www.cwa.gov.tw/Data/satellite/LCC_IR1_CR_2750/LCC_IR1_CR_2750-2026-05-12-16-00.jpg",
            source_url="https://www.cwa.gov.tw/V8/C/W/OBS_Sat.html",
            fetched_at=(datetime.now(timezone.utc) - timedelta(minutes=11)).isoformat(),
        )

        with patch("src.api.images.fetch_satellite_image") as mock_fetch:
            response = self.client.get("/api/images/latest?type=satellite")

        self.assertEqual(response.status_code, 200)
        mock_fetch.assert_called_once_with()

    def test_latest_radar_returns_image_time_from_title(self):
        insert_image(
            image_type="radar",
            source="CWA",
            title="CWA Radar Echo 2026-04-14 23:50",
            image_url="https://www.cwa.gov.tw/Data/radar/CV1_3600_202604142350.png",
            source_url="https://www.cwa.gov.tw/V8/C/W/OBS_Radar.html",
            fetched_at="2026-04-15T00:12:00+08:00",
        )

        with patch("src.api.images.fetch_radar_image") as mock_fetch:
            response = self.client.get("/api/images/latest?type=radar")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["image_time"], "2026-04-14 23:50")
        mock_fetch.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
