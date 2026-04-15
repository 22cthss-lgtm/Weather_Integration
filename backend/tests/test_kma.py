import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from flask import Flask

from src.api.images import images_bp
from src.db import get_connection, init_db
from src.jobs import fetch_850hpa_image
from src.models.image_repository import insert_image
from src.services.kma_service import KMAService


class KMAServiceTests(unittest.TestCase):
    def test_resolve_850hpa_image_url_parses_latest_image_from_html(self):
        html = """
        <html>
          <body>
            <img src="https://www.weather.go.kr/w/repositary/image/cht/img/kim_up85_anlmod_pa4_2026041512.gif">
          </body>
        </html>
        """

        with patch("src.services.kma_service.requests.get") as mock_get:
            mock_get.return_value.text = html
            mock_get.return_value.raise_for_status.return_value = None

            image_url, image_time = KMAService().resolve_850hpa_image_url()

        self.assertEqual(
            image_url,
            "https://www.weather.go.kr/w/repositary/image/cht/img/kim_up85_anlmod_pa4_2026041512.gif",
        )
        self.assertEqual(image_time, "2026-04-15 12:00")

    def test_resolve_850hpa_image_url_falls_back_to_probe(self):
        service = KMAService()

        with patch("src.services.kma_service.requests.get") as mock_get:
            mock_get.return_value.text = "<html></html>"
            mock_get.return_value.raise_for_status.return_value = None

            with patch.object(
                service,
                "resolve_latest_850hpa_image_by_probe",
                return_value=(
                    "https://www.weather.go.kr/w/repositary/image/cht/img/kim_up85_anlmod_pa4_2026041512.gif",
                    "2026-04-15 12:00",
                ),
            ) as mock_probe:
                image_url, image_time = service.resolve_850hpa_image_url()

        self.assertEqual(
            image_url,
            "https://www.weather.go.kr/w/repositary/image/cht/img/kim_up85_anlmod_pa4_2026041512.gif",
        )
        self.assertEqual(image_time, "2026-04-15 12:00")
        mock_probe.assert_called_once_with()


class Latest850hPaApiTests(unittest.TestCase):
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

    def test_latest_850hpa_returns_image_time_and_does_not_duplicate_same_image(self):
        insert_image(
            image_type="850hpa",
            source="KMA",
            title="KMA 850hPa Analysis 2026-04-15 12:00",
            image_url="https://www.weather.go.kr/w/repositary/image/cht/img/kim_up85_anlmod_pa4_2026041512.gif",
            source_url="https://www.kma.go.kr/nchn/image/chart/analysis-chart.do",
            fetched_at="2026-04-15T12:30:00+00:00",
        )

        with patch(
            "src.jobs.KMAService.resolve_850hpa_image_url",
            return_value=(
                "https://www.weather.go.kr/w/repositary/image/cht/img/kim_up85_anlmod_pa4_2026041512.gif",
                "2026-04-15 12:00",
            ),
        ):
            response = self.client.get("/api/images/latest?type=850hpa")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["image_time"], "2026-04-15 12:00")
        self.assertEqual(
            response.json["image_url"],
            "https://www.weather.go.kr/w/repositary/image/cht/img/kim_up85_anlmod_pa4_2026041512.gif",
        )

        with get_connection() as conn:
            image_count = conn.execute(
                "SELECT COUNT(*) AS count FROM images WHERE image_type = ?",
                ("850hpa",),
            ).fetchone()["count"]

        self.assertEqual(image_count, 1)

    def test_fetch_850hpa_image_inserts_new_image_when_url_changes(self):
        insert_image(
            image_type="850hpa",
            source="KMA",
            title="KMA 850hPa Analysis 2026-04-15 00:00",
            image_url="https://www.weather.go.kr/w/repositary/image/cht/img/kim_up85_anlmod_pa4_2026041500.gif",
            source_url="https://www.kma.go.kr/nchn/image/chart/analysis-chart.do",
            fetched_at="2026-04-15T01:00:00+00:00",
        )

        with patch(
            "src.jobs.KMAService.resolve_850hpa_image_url",
            return_value=(
                "https://www.weather.go.kr/w/repositary/image/cht/img/kim_up85_anlmod_pa4_2026041512.gif",
                "2026-04-15 12:00",
            ),
        ):
            fetch_850hpa_image()

        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT image_url
                FROM images
                WHERE image_type = ?
                ORDER BY fetched_at DESC
                """,
                ("850hpa",),
            ).fetchall()

        self.assertEqual(len(rows), 2)
        self.assertEqual(
            rows[0]["image_url"],
            "https://www.weather.go.kr/w/repositary/image/cht/img/kim_up85_anlmod_pa4_2026041512.gif",
        )


if __name__ == "__main__":
    unittest.main()
