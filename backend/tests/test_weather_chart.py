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


class CWAServiceWeatherChartTests(unittest.TestCase):
    def test_resolve_weather_chart_image_url_parses_latest_image_from_html(self):
        html = """
        <html>
          <body>
            <img src="/Data/fcst_img/FI04.png?t=2026041604-4">
          </body>
        </html>
        """

        with patch("src.services.cwa_service.requests.get") as mock_get:
            mock_get.return_value.ok = True
            mock_get.return_value.text = html
            mock_get.return_value.raise_for_status.return_value = None

            image_url, image_time = CWAService().resolve_weather_chart_image_url()

        self.assertEqual(
            image_url,
            "https://www.cwa.gov.tw/Data/fcst_img/FI04.png?t=2026041604-4",
        )
        self.assertEqual(image_time, "2026-04-16 04:00")

    def test_resolve_weather_chart_image_url_falls_back_to_direct_image_when_html_unavailable(self):
        service = CWAService()

        with patch("src.services.cwa_service.requests.get", side_effect=requests.RequestException("boom")):
            with patch.object(
                service,
                "resolve_direct_weather_chart_image_url",
                return_value=(
                    "https://www.cwa.gov.tw/Data/fcst_img/FI04.png?t=cache-bust",
                    None,
                ),
            ) as mock_fallback:
                image_url, image_time = service.resolve_weather_chart_image_url()

        self.assertEqual(
            image_url,
            "https://www.cwa.gov.tw/Data/fcst_img/FI04.png?t=cache-bust",
        )
        self.assertIsNone(image_time)
        mock_fallback.assert_called_once_with()


class LatestWeatherChartApiTests(unittest.TestCase):
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

    def test_latest_weather_chart_returns_image_time(self):
        insert_image(
            image_type="weather_chart",
            source="CWA",
            title="CWA Surface Weather Chart 2026-04-16 04:00",
            image_url="https://www.cwa.gov.tw/Data/fcst_img/FI04.png?t=2026041604-4",
            source_url="https://www.cwa.gov.tw/V8/C/W/analysis.html",
            fetched_at="2026-04-15T20:05:00+00:00",
        )

        with patch("src.api.images.fetch_weather_chart_image") as mock_fetch:
            response = self.client.get("/api/images/latest?type=weather_chart")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["image_time"], "2026-04-16 04:00")
        self.assertEqual(
            response.json["image_url"],
            "https://www.cwa.gov.tw/Data/fcst_img/FI04.png?t=2026041604-4",
        )
        mock_fetch.assert_called_once_with()

    def test_latest_weather_chart_skips_fetch_within_twelve_hour_ttl(self):
        insert_image(
            image_type="weather_chart",
            source="CWA",
            title="CWA Surface Weather Chart 2026-05-12 08:00",
            image_url="https://www.cwa.gov.tw/Data/fcst_img/FI04.png?t=2026051208-1",
            source_url="https://www.cwa.gov.tw/V8/C/W/analysis.html",
            fetched_at=(datetime.now(timezone.utc) - timedelta(hours=11)).isoformat(),
        )

        with patch("src.api.images.fetch_weather_chart_image") as mock_fetch:
            response = self.client.get("/api/images/latest?type=weather_chart")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["image_time"], "2026-05-12 08:00")
        mock_fetch.assert_not_called()

    def test_latest_weather_chart_falls_back_to_fetched_time_when_title_has_no_embedded_time(self):
        insert_image(
            image_type="weather_chart",
            source="CWA",
            title="CWA Surface Weather Chart",
            image_url="https://www.cwa.gov.tw/Data/fcst_img/FI04.png?t=cache-bust",
            source_url="https://www.cwa.gov.tw/V8/C/W/analysis.html",
            fetched_at="2026-04-15T20:05:00+00:00",
        )

        with patch("src.api.images.fetch_weather_chart_image") as mock_fetch:
            response = self.client.get("/api/images/latest?type=weather_chart")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["image_time"], "2026-04-15 20:05")
        mock_fetch.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
