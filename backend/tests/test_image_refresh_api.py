import importlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class ImageRefreshApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "weather.db"

        for module_name in ["app"]:
            sys.modules.pop(module_name, None)

        self.db_path_patcher = patch("src.db.DATABASE_PATH", self.database_path)
        self.services_patcher = patch("src.jobs.get_services", return_value=[])
        self.db_path_patcher.start()
        self.services_patcher.start()

        app_module = importlib.import_module("app")
        self.client = app_module.create_app().test_client()

    def tearDown(self):
        self.services_patcher.stop()
        self.db_path_patcher.stop()
        self.temp_dir.cleanup()

    def test_refresh_requires_type(self):
        response = self.client.post("/api/images/refresh")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["error"], "Query parameter 'type' is required.")

    def test_refresh_rejects_unsupported_type(self):
        response = self.client.post("/api/images/refresh?type=weather_chart")

        self.assertEqual(response.status_code, 400)
        self.assertIn("Refresh is not supported", response.json["error"])

    def test_refresh_supported_types_call_matching_fetcher(self):
        cases = [
            ("radar", "fetch_radar_image"),
            ("satellite", "fetch_satellite_image"),
            ("temperature", "fetch_temperature_image"),
            ("rainfall", "fetch_rainfall_image"),
        ]

        for image_type, fetcher_name in cases:
            with self.subTest(image_type=image_type):
                with patch(f"src.api.images.{fetcher_name}") as mock_fetch:
                    response = self.client.post(f"/api/images/refresh?type={image_type}")

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json["image_type"], image_type)
                self.assertEqual(response.json["status"], "refreshed")
                mock_fetch.assert_called_once_with()

    def test_refresh_supported_type_returns_error_when_fetch_fails(self):
        with patch("src.api.images.fetch_satellite_image", side_effect=RuntimeError("fetch failed")):
            response = self.client.post("/api/images/refresh?type=satellite")

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json["error"], "Failed to refresh satellite image.")


if __name__ == "__main__":
    unittest.main()
