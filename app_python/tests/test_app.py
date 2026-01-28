import os
import sys
import unittest


# Allow importing app_python/app.py as a module named "app"
TESTS_DIR = os.path.dirname(__file__)
APP_DIR = os.path.dirname(TESTS_DIR)
sys.path.insert(0, APP_DIR)

from app import app as flask_app  # noqa: E402


class DevOpsInfoServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        flask_app.testing = True
        cls.client = flask_app.test_client()

    def test_root_endpoint_returns_expected_structure(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.is_json)

        data = resp.get_json()
        self.assertIsInstance(data, dict)

        # Top-level keys
        for key in ("service", "system", "runtime", "request", "endpoints"):
            self.assertIn(key, data)

        # Service
        self.assertEqual(data["service"]["name"], "devops-info-service")
        self.assertEqual(data["service"]["version"], "1.0.0")
        self.assertEqual(data["service"]["framework"], "Flask")

        # System
        self.assertIn("hostname", data["system"])
        self.assertIn("platform", data["system"])
        self.assertIn("platform_version", data["system"])
        self.assertIn("architecture", data["system"])
        self.assertIn("cpu_count", data["system"])
        self.assertIn("python_version", data["system"])

        # Runtime
        self.assertGreaterEqual(int(data["runtime"]["uptime_seconds"]), 0)
        self.assertIsInstance(data["runtime"]["uptime_human"], str)
        self.assertIsInstance(data["runtime"]["current_time"], str)
        self.assertEqual(data["runtime"]["timezone"], "UTC")

        # Request
        self.assertEqual(data["request"]["method"], "GET")
        self.assertEqual(data["request"]["path"], "/")
        self.assertIn("client_ip", data["request"])
        self.assertIn("user_agent", data["request"])

        # Endpoints list
        endpoints = data["endpoints"]
        self.assertIsInstance(endpoints, list)
        paths = {e.get("path") for e in endpoints if isinstance(e, dict)}
        self.assertIn("/", paths)
        self.assertIn("/health", paths)

    def test_health_endpoint_returns_expected_payload(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.is_json)

        data = resp.get_json()
        self.assertEqual(data["status"], "healthy")
        self.assertIsInstance(data["timestamp"], str)
        self.assertGreaterEqual(int(data["uptime_seconds"]), 0)

    def test_not_found_returns_json_404(self):
        resp = self.client.get("/does-not-exist")
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(resp.is_json)

        data = resp.get_json()
        self.assertEqual(data["error"], "Not Found")
        self.assertIn("message", data)


if __name__ == "__main__":
    unittest.main()

