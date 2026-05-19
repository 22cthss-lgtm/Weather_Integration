import importlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class AppRouteTests(unittest.TestCase):
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

    def test_docs_route_is_not_registered_while_faq_still_works(self):
        docs_response = self.client.get("/api/docs")
        faq_response = self.client.get("/api/faqs")

        self.assertEqual(docs_response.status_code, 404)
        self.assertEqual(faq_response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
