import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from flask import Flask

from src.api.images import images_bp
from src.db import init_db
from src.jobs import backfill_radar_images, backfill_satellite_images
from src.models.image_repository import insert_image
from src.services.cwa_service import CWAService


class CWAServiceSatelliteAndRadarTests(unittest.TestCase):
    def test_build_satellite_image_url_uses_cwa_timestamp_pattern(self):
        image_time = datetime(2026, 5, 21, 17, 0, tzinfo=CWAService.satellite_timezone)

        image_url = CWAService().build_satellite_image_url(image_time)

        self.assertEqual(
            image_url,
            "https://www.cwa.gov.tw/Data/satellite/LCC_IR1_CR_2750/LCC_IR1_CR_2750-2026-05-21-17-00.jpg",
        )

    def test_satellite_time_slots_for_today_stop_at_latest_publishable_ten_minutes(self):
        now = datetime(2026, 5, 21, 17, 34, tzinfo=CWAService.satellite_timezone)

        slots = CWAService().satellite_time_slots_for_date(date(2026, 5, 21), now=now)

        self.assertEqual(slots[0].strftime("%Y-%m-%d %H:%M"), "2026-05-21 00:00")
        self.assertEqual(slots[-1].strftime("%Y-%m-%d %H:%M"), "2026-05-21 17:00")
        self.assertEqual(len(slots), 103)

    def test_build_radar_image_url_uses_cwa_timestamp_pattern(self):
        image_time = datetime(2026, 5, 21, 17, 0, tzinfo=CWAService.satellite_timezone)

        image_url = CWAService().build_radar_image_url(image_time)

        self.assertEqual(
            image_url,
            "https://www.cwa.gov.tw/Data/radar/CV1_3600_202605211700.png",
        )

    def test_radar_time_slots_for_today_stop_at_latest_publishable_ten_minutes(self):
        now = datetime(2026, 5, 21, 17, 24, tzinfo=CWAService.satellite_timezone)

        slots = CWAService().radar_time_slots_for_date(date(2026, 5, 21), now=now)

        self.assertEqual(slots[0].strftime("%Y-%m-%d %H:%M"), "2026-05-21 00:00")
        self.assertEqual(slots[-1].strftime("%Y-%m-%d %H:%M"), "2026-05-21 17:00")
        self.assertEqual(len(slots), 103)


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

    def test_latest_satellite_fetches_when_latest_record_exceeds_configured_ttl(self):
        insert_image(
            image_type="satellite",
            source="CWA",
            title="CWA Color Satellite Cloud 2026-05-12 16:00",
            image_url="https://www.cwa.gov.tw/Data/satellite/LCC_IR1_CR_2750/LCC_IR1_CR_2750-2026-05-12-16-00.jpg",
            source_url="https://www.cwa.gov.tw/V8/C/W/OBS_Sat.html",
            fetched_at=(datetime.now(timezone.utc) - timedelta(minutes=16)).isoformat(),
        )

        with patch("src.api.images.fetch_satellite_image") as mock_fetch:
            response = self.client.get("/api/images/latest?type=satellite")

        self.assertEqual(response.status_code, 200)
        mock_fetch.assert_called_once_with()

    def test_backfill_satellite_today_inserts_available_missing_slots(self):
        insert_image(
            image_type="satellite",
            source="CWA",
            title="CWA Color Satellite Cloud 2026-05-21 00:00",
            image_url="https://www.cwa.gov.tw/Data/satellite/LCC_IR1_CR_2750/LCC_IR1_CR_2750-2026-05-21-00-00.jpg",
            source_url="https://www.cwa.gov.tw/V8/C/W/OBS_Sat.html",
            fetched_at="2026-05-20T16:05:00+00:00",
            image_time="2026-05-21 00:00",
        )
        now = datetime(2026, 5, 21, 0, 41, tzinfo=CWAService.satellite_timezone)

        def image_exists(image_url):
            return image_url.endswith("LCC_IR1_CR_2750-2026-05-21-00-10.jpg")

        with patch.object(CWAService, "image_exists", side_effect=image_exists):
            summary = backfill_satellite_images(range_name="today", now=now)

        self.assertEqual(summary["requested"], 2)
        self.assertEqual(summary["inserted"], 1)
        self.assertEqual(summary["skipped_existing"], 1)
        self.assertEqual(summary["missing"], 0)
        self.assertEqual(summary["failed"], 0)

        response = self.client.get("/api/images/history?type=satellite&date=2026-05-21")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [(entry["image_time"], entry["source_url"]) for entry in response.json],
            [
                ("2026-05-21 00:00", "https://www.cwa.gov.tw/V8/C/W/OBS_Sat.html"),
                ("2026-05-21 00:10", "https://www.cwa.gov.tw/V8/C/W/OBS_Sat.html"),
            ],
        )

    def test_backfill_endpoint_accepts_satellite_type(self):
        with patch("src.api.images.backfill_satellite_images") as mock_backfill:
            mock_backfill.return_value = {
                "image_type": "satellite",
                "date": "2026-05-21",
                "requested": 0,
                "inserted": 0,
                "skipped_existing": 0,
                "missing": 0,
                "failed": 0,
            }

            response = self.client.post("/api/images/backfill?type=satellite&range=today")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["image_type"], "satellite")
        mock_backfill.assert_called_once_with(range_name="today", image_date=None)

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

    def test_backfill_radar_today_inserts_available_missing_slots(self):
        insert_image(
            image_type="radar",
            source="CWA",
            title="CWA Radar Echo 2026-05-21 00:00",
            image_url="https://www.cwa.gov.tw/Data/radar/CV1_3600_202605210000.png",
            source_url="https://www.cwa.gov.tw/V8/C/W/OBS_Radar.html",
            fetched_at="2026-05-20T16:05:00+00:00",
            image_time="2026-05-21 00:00",
        )
        now = datetime(2026, 5, 21, 0, 34, tzinfo=CWAService.satellite_timezone)

        def image_exists(image_url):
            return image_url.endswith("202605210010.png") or image_url.endswith("202605210030.png")

        with patch.object(CWAService, "image_exists", side_effect=image_exists):
            summary = backfill_radar_images(range_name="today", now=now)

        self.assertEqual(summary["requested"], 2)
        self.assertEqual(summary["inserted"], 1)
        self.assertEqual(summary["skipped_existing"], 1)
        self.assertEqual(summary["missing"], 0)
        self.assertEqual(summary["failed"], 0)

        response = self.client.get("/api/images/history?type=radar&date=2026-05-21")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [entry["image_time"] for entry in response.json],
            ["2026-05-21 00:00", "2026-05-21 00:10"],
        )

    def test_backfill_endpoint_accepts_radar_type(self):
        with patch("src.api.images.backfill_radar_images") as mock_backfill:
            mock_backfill.return_value = {
                "image_type": "radar",
                "date": "2026-05-21",
                "requested": 0,
                "inserted": 0,
                "skipped_existing": 0,
                "missing": 0,
                "failed": 0,
            }

            response = self.client.post("/api/images/backfill?type=radar&range=today")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["image_type"], "radar")
        mock_backfill.assert_called_once_with(range_name="today", image_date=None)


if __name__ == "__main__":
    unittest.main()
