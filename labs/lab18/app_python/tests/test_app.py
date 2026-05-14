import json
import unittest
from datetime import datetime

from app import app


class TestAppEndpoints(unittest.IsolatedAsyncioTestCase):
    async def _asgi_request(
        self,
        method: str,
        path: str,
        headers: dict[str, str] | None = None,
        client: tuple[str, int] = ("127.0.0.1", 12345),
    ) -> tuple[int, dict | str, dict[str, str]]:
        status_code: int | None = None
        response_headers: dict[str, str] = {}
        response_body = bytearray()

        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": method,
            "scheme": "http",
            "path": path,
            "raw_path": path.encode(),
            "query_string": b"",
            "root_path": "",
            "headers": [
                (name.lower().encode("utf-8"), value.encode("utf-8")) for name, value in (headers or {}).items()
            ],
            "client": client,
            "server": ("testserver", 80),
        }

        async def receive() -> dict:
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message: dict) -> None:
            nonlocal status_code, response_headers
            if message["type"] == "http.response.start":
                status_code = message["status"]
                response_headers = {
                    name.decode("utf-8").lower(): value.decode("utf-8")
                    for name, value in message.get("headers", [])
                }
            elif message["type"] == "http.response.body":
                response_body.extend(message.get("body", b""))

        await app(scope, receive, send)

        assert status_code is not None
        raw_body = response_body.decode("utf-8") if response_body else ""
        content_type = response_headers.get("content-type", "")
        payload = json.loads(raw_body) if raw_body and "application/json" in content_type else raw_body
        return status_code, payload, response_headers

    async def test_root_returns_expected_structure(self) -> None:
        status, payload, headers = await self._asgi_request("GET", "/")

        self.assertEqual(status, 200)
        self.assertIn("application/json", headers.get("content-type", ""))
        self.assertEqual(
            set(payload.keys()),
            {"service", "system", "runtime", "request", "visits", "configuration", "endpoints"},
        )

        service = payload["service"]
        self.assertEqual(service["name"], "devops-info-service")
        self.assertEqual(service["framework"], "FastAPI")
        self.assertIsInstance(service["version"], str)
        self.assertEqual(service["variant"], "primary")

        system = payload["system"]
        self.assertIsInstance(system["hostname"], str)
        self.assertIsInstance(system["platform"], str)
        self.assertIsInstance(system["python_version"], str)

        runtime = payload["runtime"]
        self.assertIsInstance(runtime["uptime_seconds"], int)
        self.assertGreaterEqual(runtime["uptime_seconds"], 0)
        self.assertIsInstance(runtime["uptime_human"], str)
        self.assertEqual(runtime["timezone"], "UTC")
        datetime.fromisoformat(runtime["current_time"])

        request_info = payload["request"]
        self.assertEqual(request_info["method"], "GET")
        self.assertEqual(request_info["path"], "/")
        self.assertIsInstance(request_info["user_agent"], str)

        visits = payload["visits"]
        self.assertIsInstance(visits["count"], int)
        self.assertGreaterEqual(visits["count"], 1)
        self.assertTrue(visits["path"].endswith("visits"))

        configuration = payload["configuration"]
        self.assertTrue(configuration["path"].endswith("config.json"))
        self.assertIsInstance(configuration["loaded"], bool)
        self.assertIsInstance(configuration["values"], dict)

        endpoints = {(item["path"], item["method"]) for item in payload["endpoints"]}
        self.assertEqual(
            endpoints,
            {("/", "GET"), ("/health", "GET"), ("/ready", "GET"), ("/visits", "GET"), ("/metrics", "GET")},
        )

    async def test_root_uses_forwarded_for_header(self) -> None:
        status, payload, _ = await self._asgi_request(
            "GET",
            "/",
            headers={
                "x-forwarded-for": "203.0.113.5",
                "user-agent": "unittest-agent",
            },
            client=("10.0.0.10", 5678),
        )

        self.assertEqual(status, 200)
        request_info = payload["request"]
        self.assertEqual(request_info["client_ip"], "203.0.113.5")
        self.assertEqual(request_info["user_agent"], "unittest-agent")

    async def test_root_falls_back_to_client_ip_without_forwarded_header(self) -> None:
        status, payload, _ = await self._asgi_request(
            "GET",
            "/",
            headers={"user-agent": "unittest-agent"},
            client=("10.0.0.11", 9876),
        )

        self.assertEqual(status, 200)
        request_info = payload["request"]
        self.assertEqual(request_info["client_ip"], "10.0.0.11")

    async def test_health_returns_expected_payload(self) -> None:
        status, payload, headers = await self._asgi_request("GET", "/health")

        self.assertEqual(status, 200)
        self.assertIn("application/json", headers.get("content-type", ""))
        self.assertEqual(payload["status"], "healthy")
        self.assertEqual(payload["service"], "devops-info-service")
        self.assertIsInstance(payload["uptime_seconds"], int)
        self.assertGreaterEqual(payload["uptime_seconds"], 0)
        datetime.fromisoformat(payload["timestamp"])

    async def test_ready_returns_expected_payload(self) -> None:
        status, payload, headers = await self._asgi_request("GET", "/ready")

        self.assertEqual(status, 200)
        self.assertIn("application/json", headers.get("content-type", ""))
        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["service"], "devops-info-service")
        datetime.fromisoformat(payload["timestamp"])

    async def test_visits_endpoint_tracks_root_requests(self) -> None:
        before_status, before_payload, _ = await self._asgi_request("GET", "/visits")
        root_status, root_payload, _ = await self._asgi_request("GET", "/")
        after_status, after_payload, _ = await self._asgi_request("GET", "/visits")

        self.assertEqual(before_status, 200)
        self.assertEqual(root_status, 200)
        self.assertEqual(after_status, 200)
        self.assertEqual(after_payload["visits"], before_payload["visits"] + 1)
        self.assertEqual(root_payload["visits"]["count"], after_payload["visits"])
        self.assertTrue(after_payload["path"].endswith("visits"))
        datetime.fromisoformat(after_payload["timestamp"])

    async def test_unknown_endpoint_returns_404(self) -> None:
        status, payload, _ = await self._asgi_request("GET", "/does-not-exist")

        self.assertEqual(status, 404)
        self.assertEqual(payload["detail"], "Not Found")

    async def test_health_rejects_post_method(self) -> None:
        status, payload, _ = await self._asgi_request("POST", "/health")

        self.assertEqual(status, 405)
        self.assertEqual(payload["detail"], "Method Not Allowed")

    async def test_metrics_endpoint_exposes_prometheus_metrics(self) -> None:
        await self._asgi_request("GET", "/")
        await self._asgi_request("GET", "/health")
        await self._asgi_request("GET", "/ready")
        await self._asgi_request("GET", "/visits")
        await self._asgi_request("GET", "/does-not-exist")
        status, payload, headers = await self._asgi_request("GET", "/metrics")

        self.assertEqual(status, 200)
        self.assertIn("text/plain", headers.get("content-type", ""))
        self.assertIsInstance(payload, str)
        self.assertIn("# HELP http_requests_total Total HTTP requests handled by the service.", payload)
        self.assertIn("# TYPE http_request_duration_seconds histogram", payload)
        self.assertIn("# TYPE http_requests_in_progress gauge", payload)
        self.assertIn('http_requests_total{endpoint="/",method="GET",status_code="200"}', payload)
        self.assertIn('http_requests_total{endpoint="/health",method="GET",status_code="200"}', payload)
        self.assertIn('http_requests_total{endpoint="/ready",method="GET",status_code="200"}', payload)
        self.assertIn('http_requests_total{endpoint="/visits",method="GET",status_code="200"}', payload)
        self.assertIn('http_requests_total{endpoint="unmatched",method="GET",status_code="404"}', payload)
        self.assertIn('devops_info_endpoint_calls_total{endpoint="/"}', payload)
        self.assertIn('devops_info_endpoint_calls_total{endpoint="/health"}', payload)
        self.assertIn('devops_info_endpoint_calls_total{endpoint="/ready"}', payload)
        self.assertIn('devops_info_endpoint_calls_total{endpoint="/visits"}', payload)
        self.assertIn("devops_info_system_info_collection_seconds_bucket", payload)
