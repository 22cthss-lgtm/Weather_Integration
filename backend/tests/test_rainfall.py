import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import requests
from flask import Flask

from src.api.images import images_bp
from src.db import init_db
from src.models.image_repository import insert_image
from src.services.cwa_service import CWAService


class CWAServiceRainfallTests(unittest.TestCase):
    def test_resolve_rainfall_image_url_parses_latest_image_from_html(self):
        html = """
        <html>
          <body>
            <img src="/Data/rainfall/2026-04-10_1730.QZJ8.jpg">
          </body>
        </html>
        """

        with patch("src.services.cwa_service.requests.get") as mock_get:
            mock_get.return_value.ok = True
            mock_get.return_value.text = html
            mock_get.return_value.raise_for_status.return_value = None

            image_url, image_time = CWAService().resolve_rainfall_image_url()

        self.assertEqual(
            image_url,
            "https://www.cwa.gov.tw/Data/rainfall/2026-04-10_1730.QZJ8.jpg",
        )
        self.assertEqual(image_time, "2026-04-10 17:30")

    def test_resolve_rainfall_image_url_falls_back_to_time_probe(self):
        service = CWAService()

        with patch("src.services.cwa_service.requests.get", side_effect=requests.RequestException("boom")):
            with patch.object(
                service,
                "resolve_latest_image",
                return_value=(
                    "https://www.cwa.gov.tw/Data/rainfall/2026-04-10_1730.QZJ8.jpg",
                    "2026-04-10 17:30",
                ),
            ) as mock_resolve_latest:
                image_url, image_time = service.resolve_rainfall_image_url()

        self.assertEqual(
            image_url,
            "https://www.cwa.gov.tw/Data/rainfall/2026-04-10_1730.QZJ8.jpg",
        )
        self.assertEqual(image_time, "2026-04-10 17:30")
        mock_resolve_latest.assert_called_once()


class LatestRainfallApiTests(unittest.TestCase):
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

    def test_latest_rainfall_returns_image_time(self):
        insert_image(
            image_type="rainfall",
            source="CWA",
            title="CWA Accumulated Rainfall 2026-04-10 17:30",
            image_url="https://www.cwa.gov.tw/Data/rainfall/2026-04-10_1730.QZJ8.jpg",
            source_url="https://www.cwa.gov.tw/V8/C/P/Rainfall/Rainfall_QZJ.html",
            fetched_at="2026-04-10T09:40:00+00:00",
        )

        with patch("src.api.images.fetch_rainfall_image") as mock_fetch:
            response = self.client.get("/api/images/latest?type=rainfall")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["image_time"], "2026-04-10 17:30")
        self.assertEqual(
            response.json["image_url"],
            "https://www.cwa.gov.tw/Data/rainfall/2026-04-10_1730.QZJ8.jpg",
        )
        mock_fetch.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
