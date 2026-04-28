import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from flask import Flask

from src.api.images import images_bp
from src.db import init_db
from src.models.image_repository import insert_image
from src.services.nsidc_service import NSIDCService


class NSIDCServiceTests(unittest.TestCase):
    def test_resolve_latest_arctic_sea_ice_images_parses_dates_from_current_assets(self):
        service = NSIDCService()

        with patch.object(
            service,
            "fetch_image_bytes",
            side_effect=[
                b"Sea Ice Extent, 08 Mar 2026",
                b"Sea Ice Concentration, 06 Apr 2026",
                b"Arctic Sea Ice Extent, Jan 1979 to 07 Apr 2026",
            ],
        ):
            payloads = service.resolve_latest_arctic_sea_ice_images()

        self.assertEqual(payloads["seaice_arctic_extent"]["image_time"], "2026-03-08 00:00")
        self.assertEqual(payloads["seaice_arctic_extent"]["image_url"], service.extent_image_url)
        self.assertEqual(payloads["seaice_arctic_concentration"]["image_time"], "2026-04-06 00:00")
        self.assertEqual(payloads["seaice_arctic_timeseries"]["image_time"], "2026-04-07 00:00")

    def test_resolve_latest_antarctic_sea_ice_images_parses_dates_from_current_assets(self):
        service = NSIDCService()

        with patch.object(
            service,
            "fetch_image_bytes",
            side_effect=[
                b"Sea Ice Extent, 11 Apr 2026",
                b"Sea Ice Concentration, 12 Apr 2026",
                b"Antarctic Sea Ice Extent, Jan 1979 to 13 Apr 2026",
            ],
        ):
            payloads = service.resolve_latest_antarctic_sea_ice_images()

        self.assertEqual(payloads["seaice_antarctic_extent"]["image_time"], "2026-04-11 00:00")
        self.assertEqual(payloads["seaice_antarctic_extent"]["image_url"], service.antarctic_extent_image_url)
        self.assertEqual(payloads["seaice_antarctic_concentration"]["image_time"], "2026-04-12 00:00")
        self.assertEqual(payloads["seaice_antarctic_timeseries"]["image_time"], "2026-04-13 00:00")

    def test_fetch_emits_arctic_titles_for_arctic_payloads(self):
        service = NSIDCService()

        with (
            patch.object(
                service,
                "resolve_latest_arctic_sea_ice_images",
                return_value={
                    "seaice_arctic_extent": {
                        "image_url": service.extent_image_url,
                        "image_time": "2026-03-08 00:00",
                    },
                    "seaice_arctic_concentration": {
                        "image_url": service.concentration_image_url,
                        "image_time": "2026-04-06 00:00",
                    },
                    "seaice_arctic_timeseries": {
                        "image_url": service.timeseries_image_url,
                        "image_time": "2026-04-07 00:00",
                    },
                },
            ),
            patch.object(service, "resolve_latest_antarctic_sea_ice_images", return_value=None),
        ):
            payloads = list(service.fetch())

        self.assertEqual(payloads[0].title, "NSIDC Arctic Sea Ice Extent 2026-03-08 00:00")
        self.assertEqual(payloads[1].title, "NSIDC Arctic Sea Ice Concentration 2026-04-06 00:00")
        self.assertEqual(payloads[2].title, "NSIDC Arctic Sea Ice Extent Time Series 2026-04-07 00:00")


class LatestSeaIceApiTests(unittest.TestCase):
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

    def test_latest_seaice_returns_404(self):
        insert_image(
            image_type="seaice_arctic_extent",
            source="NSIDC",
            title="NSIDC Arctic Sea Ice Extent 2026-03-08 00:00",
            image_url="https://nsidc.org/data/seaice_index/images/daily_images/N_daily_extent_hires.png?ts=1",
            source_url="https://nsidc.org/sea-ice-today",
            fetched_at="2026-04-17T00:10:00+00:00",
        )
        insert_image(
            image_type="seaice_arctic_concentration",
            source="NSIDC",
            title="NSIDC Arctic Sea Ice Concentration 2026-04-06 00:00",
            image_url="https://nsidc.org/data/seaice_index/images/daily_images/N_daily_concentration_hires.png?ts=1",
            source_url="https://nsidc.org/sea-ice-today",
            fetched_at="2026-04-17T00:10:01+00:00",
        )
        insert_image(
            image_type="seaice_arctic_timeseries",
            source="NSIDC",
            title="NSIDC Arctic Sea Ice Extent Time Series 2026-04-07 00:00",
            image_url="https://nsidc.org/data/seaice_index/images/daily_images/N_iqr_timeseries.png?ts=1",
            source_url="https://nsidc.org/sea-ice-today",
            fetched_at="2026-04-17T00:10:02+00:00",
        )

        with patch("src.api.images.fetch_seaice_arctic_images") as mock_fetch:
            response = self.client.get("/api/images/latest?type=seaice")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json, {"error": "Image type not found."})
        mock_fetch.assert_not_called()

    def test_latest_seaice_arctic_returns_aggregate_payload_with_arctic_type(self):
        insert_image(
            image_type="seaice_arctic_extent",
            source="NSIDC",
            title="NSIDC Arctic Sea Ice Extent 2026-03-08 00:00",
            image_url="https://nsidc.org/data/seaice_index/images/daily_images/N_daily_extent_hires.png?ts=1",
            source_url="https://nsidc.org/sea-ice-today",
            fetched_at="2026-04-17T00:10:00+00:00",
        )
        insert_image(
            image_type="seaice_arctic_concentration",
            source="NSIDC",
            title="NSIDC Arctic Sea Ice Concentration 2026-04-06 00:00",
            image_url="https://nsidc.org/data/seaice_index/images/daily_images/N_daily_concentration_hires.png?ts=1",
            source_url="https://nsidc.org/sea-ice-today",
            fetched_at="2026-04-17T00:10:01+00:00",
        )
        insert_image(
            image_type="seaice_arctic_timeseries",
            source="NSIDC",
            title="NSIDC Arctic Sea Ice Extent Time Series 2026-04-07 00:00",
            image_url="https://nsidc.org/data/seaice_index/images/daily_images/N_iqr_timeseries.png?ts=1",
            source_url="https://nsidc.org/sea-ice-today",
            fetched_at="2026-04-17T00:10:02+00:00",
        )

        with patch("src.api.images.fetch_seaice_arctic_images") as mock_fetch:
            response = self.client.get("/api/images/latest?type=seaice_arctic")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["image_type"], "seaice_arctic")
        self.assertEqual(response.json["image_url"], "https://nsidc.org/data/seaice_index/images/daily_images/N_daily_extent_hires.png?ts=1")
        self.assertEqual(response.json["image_time"], "2026-03-08 00:00")
        self.assertEqual(response.json["title"], "NSIDC Arctic Sea Ice Extent 2026-03-08 00:00")
        self.assertEqual(len(response.json["images"]), 3)
        self.assertEqual(response.json["images"][0]["title"], "NSIDC Arctic Sea Ice Extent 2026-03-08 00:00")
        self.assertEqual(response.json["images"][1]["title"], "NSIDC Arctic Sea Ice Concentration 2026-04-06 00:00")
        self.assertEqual(response.json["images"][0]["image_type"], "seaice_arctic_extent")
        self.assertEqual(response.json["images"][1]["image_type"], "seaice_arctic_concentration")
        self.assertEqual(response.json["images"][2]["image_type"], "seaice_arctic_timeseries")
        mock_fetch.assert_called_once_with()

    def test_latest_seaice_antarctic_returns_aggregate_payload_with_extent_thumbnail(self):
        insert_image(
            image_type="seaice_antarctic_extent",
            source="NSIDC",
            title="NSIDC Antarctic Sea Ice Extent 2026-04-11 00:00",
            image_url="https://nsidc.org/data/seaice_index/images/daily_images/S_daily_extent_hires.png?ts=1",
            source_url="https://nsidc.org/sea-ice-today",
            fetched_at="2026-04-19T00:10:00+00:00",
        )
        insert_image(
            image_type="seaice_antarctic_concentration",
            source="NSIDC",
            title="NSIDC Antarctic Sea Ice Concentration 2026-04-12 00:00",
            image_url="https://nsidc.org/data/seaice_index/images/daily_images/S_daily_concentration_hires.png?ts=1",
            source_url="https://nsidc.org/sea-ice-today",
            fetched_at="2026-04-19T00:10:01+00:00",
        )
        insert_image(
            image_type="seaice_antarctic_timeseries",
            source="NSIDC",
            title="NSIDC Antarctic Sea Ice Extent Time Series 2026-04-13 00:00",
            image_url="https://nsidc.org/data/seaice_index/images/daily_images/S_iqr_timeseries.png?ts=1",
            source_url="https://nsidc.org/sea-ice-today",
            fetched_at="2026-04-19T00:10:02+00:00",
        )

        with patch("src.api.images.fetch_seaice_antarctic_images") as mock_fetch:
            response = self.client.get("/api/images/latest?type=seaice_antarctic")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["image_type"], "seaice_antarctic")
        self.assertEqual(
            response.json["image_url"],
            "https://nsidc.org/data/seaice_index/images/daily_images/S_daily_extent_hires.png?ts=1",
        )
        self.assertEqual(response.json["image_time"], "2026-04-11 00:00")
        self.assertEqual(len(response.json["images"]), 3)
        self.assertEqual(response.json["images"][0]["image_type"], "seaice_antarctic_extent")
        self.assertEqual(response.json["images"][1]["image_type"], "seaice_antarctic_concentration")
        self.assertEqual(response.json["images"][2]["image_type"], "seaice_antarctic_timeseries")
        mock_fetch.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
