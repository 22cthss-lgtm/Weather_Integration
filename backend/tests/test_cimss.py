import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from flask import Flask

from src.api.images import images_bp
from src.db import init_db
from src.models.image_repository import insert_image
from src.services.cimss_service import CIMSSService


class CIMSSServiceTests(unittest.TestCase):
    def test_resolve_latest_wind_analysis_images_uses_current_page_and_last_modified_fallback(self):
        service = CIMSSService()
        page_response = Mock()
        page_response.raise_for_status.return_value = None
        page_response.text = """
        <html>
          <body>
            <img src="westpac/winds/wgmsshr.GIF" alt="">
            <a href="https://tropic.ssec.wisc.edu/real-time/westpac/winds/wgmsshr.GIF">direct</a>
          </body>
        </html>
        """

        shear_response = Mock()
        shear_response.raise_for_status.return_value = None
        shear_response.content = b"GIF89a no embedded time"
        shear_response.headers = {"Last-Modified": "Tue, 15 Apr 2026 00:00:00 GMT"}

        vorticity_response = Mock()
        vorticity_response.raise_for_status.return_value = None
        vorticity_response.content = b"GIF89a still no embedded time"
        vorticity_response.headers = {"Last-Modified": "Tue, 15 Apr 2026 00:00:00 GMT"}

        with patch(
            "src.services.cimss_service.requests.get",
            side_effect=[page_response, shear_response, vorticity_response],
        ):
            with patch.object(service, "cache_buster", return_value=1776211200):
                resolved = service.resolve_latest_wind_analysis_images()

        self.assertEqual(
            resolved,
            {
                "cimss_wind_shear": {
                    "image_url": "https://tropic.ssec.wisc.edu/real-time/westpac/winds/wgmsshr.GIF?ts=1776211200",
                    "image_time": "2026-04-15 00:00",
                },
                "cimss_850mb_vorticity": {
                    "image_url": "https://tropic.ssec.wisc.edu/real-time/westpac/winds/wgmsvor.GIF?ts=1776211200",
                    "image_time": "2026-04-15 00:00",
                },
            },
        )

    def test_extract_image_time_from_bytes_prefers_embedded_timestamp(self):
        service = CIMSSService()

        image_time = service.extract_image_time_from_bytes(
            b"GIF89a Analysis Time 00 UTC 15 APR 2026 generated"
        )

        self.assertEqual(image_time, "2026-04-15 00:00")


class LatestCIMSSWindAnalysisApiTests(unittest.TestCase):
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

    def test_latest_cimss_wind_analysis_returns_grouped_payload_with_shear_thumbnail(self):
        insert_image(
            image_type="cimss_wind_shear",
            source="CIMSS",
            title="CIMSS Wind Shear 2026-04-15 00:00",
            image_url="https://tropic.ssec.wisc.edu/real-time/westpac/winds/wgmsshr.GIF?ts=1",
            source_url="https://tropic.ssec.wisc.edu/real-time/windmain.php?&basin=westpac&sat=wgms&prod=shr&zoom=&time=",
            fetched_at="2026-04-19T12:00:00+00:00",
        )
        insert_image(
            image_type="cimss_850mb_vorticity",
            source="CIMSS",
            title="CIMSS 850mb Vorticity 2026-04-15 00:00",
            image_url="https://tropic.ssec.wisc.edu/real-time/westpac/winds/wgmsvor.GIF?ts=1",
            source_url="https://tropic.ssec.wisc.edu/real-time/windmain.php?&basin=westpac&sat=wgms&prod=shr&zoom=&time=",
            fetched_at="2026-04-19T12:00:01+00:00",
        )

        with patch("src.api.images.fetch_cimss_wind_analysis_images") as mock_fetch:
            response = self.client.get("/api/images/latest?type=cimss_wind_analysis")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["image_type"], "cimss_wind_analysis")
        self.assertEqual(
            response.json["image_url"],
            "https://tropic.ssec.wisc.edu/real-time/westpac/winds/wgmsshr.GIF?ts=1",
        )
        self.assertEqual(response.json["image_time"], "2026-04-15 00:00")
        self.assertEqual(len(response.json["images"]), 2)
        self.assertEqual(response.json["images"][0]["image_type"], "cimss_wind_shear")
        self.assertEqual(response.json["images"][1]["image_type"], "cimss_850mb_vorticity")
        mock_fetch.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
