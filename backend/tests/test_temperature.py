import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import requests
from flask import Flask

from src.api.images import images_bp
from src.db import init_db
from src.models.image_repository import insert_image
from src.services.cwa_service import CWAService


class CWAServiceTemperatureTests(unittest.TestCase):
    def test_resolve_temperature_image_url_parses_latest_image_from_html(self):
        html = """
        <html>
          <body>
            <img src="/Data/temperature/2026-04-10_1700.GTP8w.jpg">
          </body>
        </html>
        """

        with patch("src.services.cwa_service.requests.get") as mock_get:
            mock_get.return_value.ok = True
            mock_get.return_value.text = html
            mock_get.return_value.raise_for_status.return_value = None

            image_url, image_time = CWAService().resolve_temperature_image_url()

        self.assertEqual(
            image_url,
            "https://www.cwa.gov.tw/Data/temperature/2026-04-10_1700.GTP8w.jpg",
        )
        self.assertEqual(image_time, "2026-04-10 17:00")

    def test_resolve_temperature_image_url_falls_back_to_time_probe(self):
        service = CWAService()

        with patch("src.services.cwa_service.requests.get", side_effect=requests.RequestException("boom")):
            with patch.object(
                service,
                "resolve_latest_image",
                return_value=(
                    "https://www.cwa.gov.tw/Data/temperature/2026-04-10_1700.GTP8w.jpg",
                    "2026-04-10 17:00",
                ),
            ) as mock_resolve_latest:
                image_url, image_time = service.resolve_temperature_image_url()

        self.assertEqual(
            image_url,
            "https://www.cwa.gov.tw/Data/temperature/2026-04-10_1700.GTP8w.jpg",
        )
        self.assertEqual(image_time, "2026-04-10 17:00")
        mock_resolve_latest.assert_called_once()


class LatestTemperatureApiTests(unittest.TestCase):
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

    def test_latest_temperature_returns_image_time(self):
        insert_image(
            image_type="temperature",
            source="CWA",
            title="CWA Temperature Distribution 2026-04-10 17:00",
            image_url="https://www.cwa.gov.tw/Data/temperature/2026-04-10_1700.GTP8w.jpg",
            source_url="https://www.cwa.gov.tw/V8/C/W/OBS_Temp.html",
            fetched_at="2026-04-10T09:00:00+00:00",
        )

        with patch("src.api.images.fetch_temperature_image") as mock_fetch:
            response = self.client.get("/api/images/latest?type=temperature")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["image_time"], "2026-04-10 17:00")
        self.assertEqual(
            response.json["image_url"],
            "https://www.cwa.gov.tw/Data/temperature/2026-04-10_1700.GTP8w.jpg",
        )
        mock_fetch.assert_called_once_with()

    def test_latest_temperature_skips_fetch_within_one_hour_ttl(self):
        insert_image(
            image_type="temperature",
            source="CWA",
            title="CWA Temperature Distribution 2026-05-12 17:00",
            image_url="https://www.cwa.gov.tw/Data/temperature/2026-05-12_1700.GTP8w.jpg",
            source_url="https://www.cwa.gov.tw/V8/C/W/OBS_Temp.html",
            fetched_at=(datetime.now(timezone.utc) - timedelta(minutes=45)).isoformat(),
        )

        with patch("src.api.images.fetch_temperature_image") as mock_fetch:
            response = self.client.get("/api/images/latest?type=temperature")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["image_time"], "2026-05-12 17:00")
        mock_fetch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
