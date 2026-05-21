import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from flask import Flask

from src.api.rainfall import rainfall_bp
from src.db import init_db
from src.models.rainfall_observation_repository import (
    get_latest_rainfall_fetched_at,
    get_top_rainfall_observations,
    upsert_rainfall_observations,
)
from src.services.rainfall_observation_service import (
    CWA_API_KEY_MISSING_MESSAGE,
    parse_cwa_rainfall_response,
    parse_rainfall_number,
)


class RainfallObservationParsingTests(unittest.TestCase):
    def test_parse_rainfall_number_accepts_numeric_values_only(self):
        self.assertEqual(parse_rainfall_number("12.5"), 12.5)
        self.assertEqual(parse_rainfall_number(0), 0.0)
        self.assertIsNone(parse_rainfall_number("X"))
        self.assertIsNone(parse_rainfall_number(""))
        self.assertIsNone(parse_rainfall_number(None))
        self.assertIsNone(parse_rainfall_number("-99"))
        self.assertIsNone(parse_rainfall_number("-98"))
        self.assertIsNone(parse_rainfall_number("T"))

    def test_parse_cwa_rainfall_response_maps_station_and_rainfall_fields(self):
        payload = {
            "records": {
                "Station": [
                    {
                        "StationName": "阿里山",
                        "StationId": "C0M530",
                        "ObsTime": {"DateTime": "2026-05-19T13:10:00+08:00"},
                        "GeoInfo": {
                            "Coordinates": [
                                {
                                    "CoordinateName": "WGS84",
                                    "StationLatitude": "23.508",
                                    "StationLongitude": "120.813",
                                }
                            ],
                            "StationAltitude": "2413.4",
                            "CountyName": "嘉義縣",
                            "TownName": "阿里山鄉",
                        },
                        "RainfallElement": {
                            "Now": {"Precipitation": "28.5"},
                            "Past10Min": {"Precipitation": "1.5"},
                            "Past1hr": {"Precipitation": "12.0"},
                            "Past3hr": {"Precipitation": "X"},
                            "Past6Hr": {"Precipitation": "18.0"},
                            "Past12hr": {"Precipitation": "25.0"},
                            "Past24hr": {"Precipitation": "64.5"},
                            "Past2days": {"Precipitation": "88.0"},
                            "Past3days": {"Precipitation": ""},
                        },
                    }
                ]
            }
        }

        observations = parse_cwa_rainfall_response(payload, fetched_at="2026-05-19T05:15:00+00:00")

        self.assertEqual(len(observations), 1)
        observation = observations[0]
        self.assertEqual(observation["station_id"], "C0M530")
        self.assertEqual(observation["station_name"], "阿里山")
        self.assertEqual(observation["county"], "嘉義縣")
        self.assertEqual(observation["town"], "阿里山鄉")
        self.assertEqual(observation["observed_at"], "2026-05-19T13:10:00+08:00")
        self.assertEqual(observation["rain_10min"], 1.5)
        self.assertEqual(observation["rain_1hr"], 12.0)
        self.assertIsNone(observation["rain_3hr"])
        self.assertEqual(observation["rain_6hr"], 18.0)
        self.assertEqual(observation["rain_12hr"], 25.0)
        self.assertEqual(observation["rain_24hr"], 64.5)
        self.assertEqual(observation["rain_today"], 28.5)
        self.assertEqual(observation["rain_1day"], 88.0)
        self.assertIsNone(observation["rain_2days"])


class RainfallObservationRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "weather.db"

        self.db_path_patcher = patch("src.db.DATABASE_PATH", self.database_path)
        self.db_path_patcher.start()
        init_db()

    def tearDown(self):
        self.db_path_patcher.stop()
        self.temp_dir.cleanup()

    def test_upsert_deduplicates_station_and_observed_time(self):
        observation = {
            "station_id": "C0M530",
            "station_name": "阿里山",
            "county": "嘉義縣",
            "town": "阿里山鄉",
            "latitude": 23.508,
            "longitude": 120.813,
            "elevation": 2413.4,
            "observed_at": "2026-05-19T13:10:00+08:00",
            "rain_10min": 1.5,
            "rain_1hr": 12.0,
            "rain_3hr": None,
            "rain_6hr": None,
            "rain_12hr": 25.0,
            "rain_24hr": 64.5,
            "rain_today": 28.5,
            "rain_1day": 88.0,
            "rain_2days": None,
            "fetched_at": "2026-05-19T05:15:00+00:00",
        }
        upsert_rainfall_observations([observation])

        updated = dict(observation)
        updated["rain_10min"] = 3.0
        updated["fetched_at"] = "2026-05-19T05:25:00+00:00"
        upsert_rainfall_observations([updated])

        rows = get_top_rainfall_observations("10min", limit=10)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["rainfall"], 3.0)
        self.assertEqual(get_latest_rainfall_fetched_at(), "2026-05-19T05:25:00+00:00")

    def test_get_top_rainfall_observations_uses_latest_fetch_and_numeric_values(self):
        base = {
            "station_name": "Station",
            "county": "County",
            "town": "Town",
            "latitude": None,
            "longitude": None,
            "elevation": None,
            "observed_at": "2026-05-19T13:10:00+08:00",
            "rain_10min": None,
            "rain_1hr": None,
            "rain_3hr": None,
            "rain_6hr": None,
            "rain_12hr": None,
            "rain_24hr": None,
            "rain_today": None,
            "rain_1day": None,
            "rain_2days": None,
            "fetched_at": "2026-05-19T05:15:00+00:00",
        }
        upsert_rainfall_observations([
            {**base, "station_id": "old", "rain_1hr": 99.0},
            {**base, "station_id": "a", "rain_1hr": 2.0, "fetched_at": "2026-05-19T05:25:00+00:00"},
            {**base, "station_id": "b", "rain_1hr": None, "fetched_at": "2026-05-19T05:25:00+00:00"},
            {**base, "station_id": "c", "rain_1hr": 8.0, "fetched_at": "2026-05-19T05:25:00+00:00"},
        ])

        rows = get_top_rainfall_observations("1hr", limit=10)

        self.assertEqual([row["station_id"] for row in rows], ["c", "a"])
        self.assertEqual([row["rainfall"] for row in rows], [8.0, 2.0])


class RainfallObservationApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "weather.db"

        self.db_path_patcher = patch("src.db.DATABASE_PATH", self.database_path)
        self.db_path_patcher.start()
        init_db()

        app = Flask(__name__)
        app.register_blueprint(rainfall_bp, url_prefix="/api/rainfall")
        self.client = app.test_client()

    def tearDown(self):
        self.db_path_patcher.stop()
        self.temp_dir.cleanup()

    def test_top_endpoint_rejects_unknown_metric(self):
        response = self.client.get("/api/rainfall/top?metric=bad")

        self.assertEqual(response.status_code, 400)
        self.assertIn("Unsupported rainfall metric", response.json["error"])

    def test_top_endpoint_reports_missing_api_key_when_refresh_needed(self):
        with patch("src.services.rainfall_observation_service.os.getenv", return_value=None):
            response = self.client.get("/api/rainfall/top?metric=10min")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json["error"], CWA_API_KEY_MISSING_MESSAGE)

    def test_service_fetches_cwa_open_data_with_existing_cwa_ssl_policy(self):
        payload = {
            "records": {
                "Station": [
                    {
                        "StationName": "阿里山",
                        "StationId": "C0M530",
                        "ObsTime": {"DateTime": "2026-05-19T13:10:00+08:00"},
                        "GeoInfo": {"Coordinates": [], "CountyName": "嘉義縣", "TownName": "阿里山鄉"},
                        "RainfallElement": {"Past10Min": {"Precipitation": "1.5"}},
                    }
                ]
            }
        }

        with patch("src.services.rainfall_observation_service.os.getenv", return_value="test-key"):
            with patch("src.services.rainfall_observation_service.requests.get") as mock_get:
                mock_get.return_value.raise_for_status.return_value = None
                mock_get.return_value.json.return_value = payload

                from src.services.rainfall_observation_service import RainfallObservationService

                observations = RainfallObservationService().fetch_observations()

        self.assertEqual(observations[0]["station_id"], "C0M530")
        self.assertFalse(mock_get.call_args.kwargs["verify"])


if __name__ == "__main__":
    unittest.main()
