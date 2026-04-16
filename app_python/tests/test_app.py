import os
import shutil
import sys
import tempfile
import unittest


# Allow importing app_python/app.py as a module named "app"
TESTS_DIR = os.path.dirname(__file__)
APP_DIR = os.path.dirname(TESTS_DIR)
TEST_TMP_DIR = tempfile.mkdtemp(prefix="devops-info-tests-")
os.environ["VISITS_FILE"] = os.path.join(TEST_TMP_DIR, "visits")
sys.path.insert(0, APP_DIR)

import app as app_module  # noqa: E402


flask_app = app_module.app


class DevOpsInfoServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        flask_app.testing = True
        cls.client = flask_app.test_client()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_TMP_DIR, ignore_errors=True)

    def setUp(self):
        if os.path.exists(app_module.VISITS_FILE):
            os.remove(app_module.VISITS_FILE)

    def test_root_endpoint_returns_expected_structure(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.is_json)

        data = resp.get_json()
        self.assertIsInstance(data, dict)

        # Top-level keys
        for key in (
            "service",
            "configuration",
            "system",
            "runtime",
            "visits",
            "request",
            "endpoints",
        ):
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

        # Configuration and persistence
        self.assertEqual(data["configuration"]["config_path"], app_module.CONFIG_PATH)
        self.assertIsInstance(data["configuration"]["config_file"], dict)
        self.assertEqual(data["visits"]["count"], 1)
        self.assertEqual(data["visits"]["storage_file"], app_module.VISITS_FILE)

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
        self.assertIn("/ready", paths)
        self.assertIn("/visits", paths)

    def test_health_endpoint_returns_expected_payload(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.is_json)

        data = resp.get_json()
        self.assertEqual(data["status"], "healthy")
        self.assertIsInstance(data["timestamp"], str)
        self.assertGreaterEqual(int(data["uptime_seconds"]), 0)

    def test_ready_endpoint_returns_expected_payload(self):
        resp = self.client.get("/ready")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.is_json)

        data = resp.get_json()
        self.assertEqual(data["status"], "ready")
        self.assertIsInstance(data["timestamp"], str)
        self.assertGreaterEqual(int(data["uptime_seconds"]), 0)

    def test_not_found_returns_json_404(self):
        resp = self.client.get("/does-not-exist")
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(resp.is_json)

        data = resp.get_json()
        self.assertEqual(data["error"], "Not Found")
        self.assertIn("message", data)

    def test_metrics_endpoint_exposes_prometheus_metrics(self):
        # Generate a few requests so metrics have data points.
        self.client.get("/")
        self.client.get("/health")
        self.client.get("/ready")

        resp = self.client.get("/metrics")
        self.assertEqual(resp.status_code, 200)

        body = resp.get_data(as_text=True)
        self.assertIn("# HELP http_requests_total", body)
        self.assertIn("# TYPE http_requests_total counter", body)
        self.assertIn("http_request_duration_seconds", body)
        self.assertIn("http_requests_in_progress", body)
        self.assertIn("devops_info_endpoint_calls_total", body)
        self.assertIn("devops_info_system_collection_seconds", body)

    def test_visits_endpoint_returns_persisted_counter(self):
        first_visits = self.client.get("/visits")
        self.assertEqual(first_visits.status_code, 200)
        self.assertEqual(first_visits.get_json()["count"], 0)

        self.client.get("/")
        self.client.get("/")

        second_visits = self.client.get("/visits")
        self.assertEqual(second_visits.status_code, 200)
        self.assertEqual(second_visits.get_json()["count"], 2)

        with open(app_module.VISITS_FILE, "r", encoding="utf-8") as visits_file:
            self.assertEqual(visits_file.read().strip(), "2")


if __name__ == "__main__":
    unittest.main()
