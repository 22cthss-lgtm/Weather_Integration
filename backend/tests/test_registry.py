import unittest
from src.services.registry import get_services


class ServiceRegistryTests(unittest.TestCase):
    def test_registry_excludes_unimplemented_aqi_and_reservoir_services(self):
        service_names = {type(service).__name__ for service in get_services()}

        self.assertNotIn("AQIService", service_names)
        self.assertNotIn("ReservoirService", service_names)
        self.assertEqual(
            service_names,
            {
                "CWAService",
                "KMAService",
                "OceanService",
                "NSIDCService",
                "NCDRService",
                "SSECService",
                "MeteologixService",
            },
        )


if __name__ == "__main__":
    unittest.main()
