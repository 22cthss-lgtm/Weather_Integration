import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch

import requests
from flask import Flask

from src.api.images import images_bp
from src.db import init_db
from src.jobs import backfill_rainfall_images
from src.models.image_repository import insert_image
from src.services.cwa_service import CWAService


class CWAServiceRainfallTests(unittest.TestCase):
    def test_build_rainfall_image_url_uses_cwa_timestamp_pattern(self):
        image_time = datetime(2026, 5, 13, 19, 0, tzinfo=CWAService.satellite_timezone)

        image_url = CWAService().build_rainfall_image_url(image_time)

        self.assertEqual(
            image_url,
            "https://www.cwa.gov.tw/Data/rainfall/2026-05-13_1900.QZJ8.jpg",
        )

    def test_rainfall_time_slots_for_today_stop_at_latest_publishable_half_hour(self):
        now = datetime(2026, 5, 13, 19, 28, tzinfo=CWAService.satellite_timezone)

        slots = CWAService().rainfall_time_slots_for_date(date(2026, 5, 13), now=now)

        self.assertEqual(slots[0].strftime("%Y-%m-%d %H:%M"), "2026-05-13 00:30")
        self.assertEqual(slots[-1].strftime("%Y-%m-%d %H:%M"), "2026-05-13 19:00")
        self.assertEqual(len(slots), 38)

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

    def test_latest_rainfall_prefers_newest_image_time_over_newest_fetched_at(self):
        insert_image(
            image_type="rainfall",
            source="CWA",
            title="CWA Accumulated Rainfall 2026-05-13 19:00",
            image_url="https://www.cwa.gov.tw/Data/rainfall/2026-05-13_1900.QZJ8.jpg",
            source_url="https://www.cwa.gov.tw/V8/C/P/Rainfall/Rainfall_QZJ.html",
            fetched_at="2026-05-13T11:10:00+00:00",
            image_time="2026-05-13 19:00",
        )
        insert_image(
            image_type="rainfall",
            source="CWA",
            title="CWA Accumulated Rainfall 2026-05-13 00:30",
            image_url="https://www.cwa.gov.tw/Data/rainfall/2026-05-13_0030.QZJ8.jpg",
            source_url="https://www.cwa.gov.tw/V8/C/P/Rainfall/Rainfall_QZJ.html",
            fetched_at="2026-05-13T11:20:00+00:00",
            image_time="2026-05-13 00:30",
        )

        with patch("src.api.images.fetch_rainfall_image") as mock_fetch:
            response = self.client.get("/api/images/latest?type=rainfall")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["image_time"], "2026-05-13 19:00")
        self.assertEqual(
            response.json["image_url"],
            "https://www.cwa.gov.tw/Data/rainfall/2026-05-13_1900.QZJ8.jpg",
        )
        mock_fetch.assert_called_once_with()

    def test_latest_rainfall_includes_legacy_rows_without_stored_image_time(self):
        insert_image(
            image_type="rainfall",
            source="CWA",
            title="CWA Accumulated Rainfall 2026-05-13 19:30",
            image_url="https://www.cwa.gov.tw/Data/rainfall/2026-05-13_1930.QZJ8.jpg",
            source_url="https://www.cwa.gov.tw/V8/C/P/Rainfall/Rainfall_QZJ.html",
            fetched_at="2026-05-13T11:35:00+00:00",
        )
        insert_image(
            image_type="rainfall",
            source="CWA",
            title="CWA Accumulated Rainfall 2026-05-13 19:00",
            image_url="https://www.cwa.gov.tw/Data/rainfall/2026-05-13_1900.QZJ8.jpg",
            source_url="https://www.cwa.gov.tw/V8/C/P/Rainfall/Rainfall_QZJ.html",
            fetched_at="2026-05-13T12:08:00+00:00",
            image_time="2026-05-13 19:00",
        )

        with patch("src.api.images.fetch_rainfall_image") as mock_fetch:
            response = self.client.get("/api/images/latest?type=rainfall")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["image_time"], "2026-05-13 19:30")
        self.assertEqual(
            response.json["image_url"],
            "https://www.cwa.gov.tw/Data/rainfall/2026-05-13_1930.QZJ8.jpg",
        )
        mock_fetch.assert_called_once_with()

    def test_rainfall_history_can_filter_by_image_date(self):
        insert_image(
            image_type="rainfall",
            source="CWA",
            title="CWA Accumulated Rainfall 2026-05-13 00:30",
            image_url="https://www.cwa.gov.tw/Data/rainfall/2026-05-13_0030.QZJ8.jpg",
            source_url="https://www.cwa.gov.tw/V8/C/P/Rainfall/Rainfall_QZJ.html",
            fetched_at="2026-05-13T00:40:00+00:00",
            image_time="2026-05-13 00:30",
        )
        insert_image(
            image_type="rainfall",
            source="CWA",
            title="CWA Accumulated Rainfall 2026-05-13 01:00",
            image_url="https://www.cwa.gov.tw/Data/rainfall/2026-05-13_0100.QZJ8.jpg",
            source_url="https://www.cwa.gov.tw/V8/C/P/Rainfall/Rainfall_QZJ.html",
            fetched_at="2026-05-13T01:10:00+00:00",
            image_time="2026-05-13 01:00",
        )
        insert_image(
            image_type="rainfall",
            source="CWA",
            title="CWA Accumulated Rainfall 2026-05-12 23:30",
            image_url="https://www.cwa.gov.tw/Data/rainfall/2026-05-12_2330.QZJ8.jpg",
            source_url="https://www.cwa.gov.tw/V8/C/P/Rainfall/Rainfall_QZJ.html",
            fetched_at="2026-05-12T23:40:00+00:00",
            image_time="2026-05-12 23:30",
        )

        response = self.client.get("/api/images/history?type=rainfall&date=2026-05-13")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([entry["image_time"] for entry in response.json], ["2026-05-13 00:30", "2026-05-13 01:00"])

    def test_rainfall_history_includes_legacy_rows_without_stored_image_time(self):
        insert_image(
            image_type="rainfall",
            source="CWA",
            title="CWA Accumulated Rainfall 2026-05-13 19:30",
            image_url="https://www.cwa.gov.tw/Data/rainfall/2026-05-13_1930.QZJ8.jpg",
            source_url="https://www.cwa.gov.tw/V8/C/P/Rainfall/Rainfall_QZJ.html",
            fetched_at="2026-05-13T11:35:00+00:00",
        )

        response = self.client.get("/api/images/history?type=rainfall&date=2026-05-13")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([entry["image_time"] for entry in response.json], ["2026-05-13 19:30"])

    def test_rainfall_history_deduplicates_legacy_and_new_rows_for_same_image_time(self):
        insert_image(
            image_type="rainfall",
            source="CWA",
            title="CWA Accumulated Rainfall 2026-05-13 19:30",
            image_url="https://www.cwa.gov.tw/Data/rainfall/2026-05-13_1930.QZJ8.jpg",
            source_url="https://www.cwa.gov.tw/V8/C/P/Rainfall/Rainfall_QZJ.html",
            fetched_at="2026-05-13T11:35:00+00:00",
        )
        insert_image(
            image_type="rainfall",
            source="CWA",
            title="CWA Accumulated Rainfall 2026-05-13 20:00",
            image_url="https://www.cwa.gov.tw/Data/rainfall/2026-05-13_2000.QZJ8.jpg",
            source_url="https://www.cwa.gov.tw/V8/C/P/Rainfall/Rainfall_QZJ.html",
            fetched_at="2026-05-13T11:40:00+00:00",
            image_time="2026-05-13 20:00",
        )
        insert_image(
            image_type="rainfall",
            source="CWA",
            title="CWA Accumulated Rainfall 2026-05-13 19:30",
            image_url="https://www.cwa.gov.tw/Data/rainfall/2026-05-13_1930.QZJ8.jpg",
            source_url="https://www.cwa.gov.tw/V8/C/P/Rainfall/Rainfall_QZJ.html",
            fetched_at="2026-05-13T12:08:00+00:00",
            image_time="2026-05-13 19:30",
        )

        response = self.client.get("/api/images/history?type=rainfall&date=2026-05-13")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([entry["image_time"] for entry in response.json], ["2026-05-13 19:30", "2026-05-13 20:00"])
        self.assertEqual(response.json[0]["fetched_at"], "2026-05-13T12:08:00+00:00")

    def test_backfill_rainfall_today_inserts_available_missing_slots(self):
        insert_image(
            image_type="rainfall",
            source="CWA",
            title="CWA Accumulated Rainfall 2026-05-13 00:30",
            image_url="https://www.cwa.gov.tw/Data/rainfall/2026-05-13_0030.QZJ8.jpg",
            source_url="https://www.cwa.gov.tw/V8/C/P/Rainfall/Rainfall_QZJ.html",
            fetched_at="2026-05-13T00:40:00+00:00",
            image_time="2026-05-13 00:30",
        )
        now = datetime(2026, 5, 13, 1, 25, tzinfo=CWAService.satellite_timezone)

        def image_exists(image_url):
            return image_url.endswith("0100.QZJ8.jpg")

        with patch.object(CWAService, "image_exists", side_effect=image_exists):
            summary = backfill_rainfall_images(range_name="today", now=now)

        self.assertEqual(summary["requested"], 2)
        self.assertEqual(summary["inserted"], 1)
        self.assertEqual(summary["skipped_existing"], 1)
        self.assertEqual(summary["missing"], 0)

        response = self.client.get("/api/images/history?type=rainfall&date=2026-05-13")
        self.assertEqual([entry["image_time"] for entry in response.json], ["2026-05-13 00:30", "2026-05-13 01:00"])

    def test_backfill_rainfall_today_also_inserts_daily_representative_images(self):
        now = datetime(2026, 5, 13, 1, 25, tzinfo=CWAService.satellite_timezone)

        def image_exists(image_url):
            return image_url.endswith("2026-05-13_0000.QZJ8.jpg") or image_url.endswith("2026-05-12_0000.QZJ8.jpg")

        with patch.object(CWAService, "image_exists", side_effect=image_exists):
            summary = backfill_rainfall_images(range_name="today", now=now)

        self.assertEqual(summary["daily_representatives"]["requested"], 2)
        self.assertEqual(summary["daily_representatives"]["inserted"], 2)
        self.assertEqual(summary["daily_representatives"]["missing"], 0)

        response = self.client.get("/api/images/daily?type=rainfall&date=2026-05-13")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [(entry["label"], entry["represented_date"], entry["image_time"]) for entry in response.json],
            [
                ("Yesterday Full-Day Rainfall", "2026-05-12", "2026-05-13 00:00"),
                ("Day Before Yesterday Full-Day Rainfall", "2026-05-11", "2026-05-12 00:00"),
            ],
        )

    def test_rainfall_daily_endpoint_returns_only_existing_representatives(self):
        insert_image(
            image_type="rainfall",
            source="CWA",
            title="CWA Accumulated Rainfall 2026-05-13 00:00",
            image_url="https://www.cwa.gov.tw/Data/rainfall/2026-05-13_0000.QZJ8.jpg",
            source_url="https://www.cwa.gov.tw/V8/C/P/Rainfall/Rainfall_QZJ.html",
            fetched_at="2026-05-13T00:05:00+00:00",
            image_time="2026-05-13 00:00",
        )

        response = self.client.get("/api/images/daily?type=rainfall&date=2026-05-13")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 1)
        self.assertEqual(response.json[0]["label"], "Yesterday Full-Day Rainfall")
        self.assertEqual(response.json[0]["represented_date"], "2026-05-12")

    def test_backfill_endpoint_rejects_non_rainfall_type(self):
        response = self.client.post("/api/images/backfill?type=radar&range=today")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["error"], "Backfill is only supported for rainfall.")


if __name__ == "__main__":
    unittest.main()
