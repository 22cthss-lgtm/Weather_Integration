import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from flask import Flask

from src.api.images import images_bp
from src.db import init_db
from src.models.image_repository import insert_image
from src.services.cwa_service import CWAService


class CWAServicetchpTests(unittest.TestCase):
    def test_resolve_tchp_image_url_parses_latest_image_from_js(self):
        js = """
        var TDD_TCHP = '2026-04-13_TCHP_ostia.png';
        var TDD_TCHP_S = '2026-04-13_TCHP_Small_ostia.png';
        """

        with patch("src.services.cwa_service.requests.get") as mock_get:
            mock_get.return_value.ok = True
            mock_get.return_value.text = js
            mock_get.return_value.raise_for_status.return_value = None

            image_url, image_time = CWAService().resolve_tchp_image_url()

        self.assertTrue(
            image_url.startswith("https://www.cwa.gov.tw/Data/TCHP/2026-04-13_TCHP_ostia.png?T=")
        )
        self.assertEqual(image_time, "2026-04-13 00:00")


class LatestTCHPApiTests(unittest.TestCase):
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

    def test_latest_tchp_returns_image_time(self):
        insert_image(
            image_type="tchp",
            source="CWA",
            title="CWA TCHP 2026-04-13 00:00",
            image_url="https://www.cwa.gov.tw/Data/TCHP/2026-04-13_TCHP_ostia.png?T=2026041704-2",
            source_url="https://www.cwa.gov.tw/V8/C/W/analysis.html",
            fetched_at="2026-04-17T04:10:00+00:00",
        )

        with patch("src.api.images.fetch_tchp_image") as mock_fetch:
            response = self.client.get("/api/images/latest?type=tchp")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["image_time"], "2026-04-13 00:00")
        self.assertEqual(
            response.json["image_url"],
            "https://www.cwa.gov.tw/Data/TCHP/2026-04-13_TCHP_ostia.png?T=2026041704-2",
        )
        mock_fetch.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
