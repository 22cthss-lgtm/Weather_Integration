import unittest
from src.services.registry import get_services


class ServiceRegistryTests(unittest.TestCase):
    def test_registry_excludes_unimplemented_and_placeholder_services(self):
        service_names = {type(service).__name__ for service in get_services()}

        self.assertNotIn("AQIService", service_names)
        self.assertNotIn("ReservoirService", service_names)
        self.assertNotIn("NCDRService", service_names)
        self.assertNotIn("SSECService", service_names)
        self.assertNotIn("MeteologixService", service_names)
        self.assertEqual(
            service_names,
            {
                "CWAService",
                "KMAService",
                "OceanService",
                "NSIDCService",
            },
        )


if __name__ == "__main__":
    unittest.main()
