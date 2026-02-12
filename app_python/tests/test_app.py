"""
Unit tests for the DevOps Info Service.

Testing framework: pytest with FastAPI TestClient (httpx-based).
Covers all endpoints, response structures, data types, and error handling.
"""

import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


# ─── GET / endpoint tests ───────────────────────────────────────────


class TestRootEndpoint:
    """Tests for the GET / endpoint."""

    def test_returns_200(self, client):
        """Root endpoint should return HTTP 200."""
        response = client.get("/")
        assert response.status_code == 200

    def test_returns_json(self, client):
        """Root endpoint should return valid JSON."""
        response = client.get("/")
        assert response.headers["content-type"] == "application/json"
        data = response.json()
        assert isinstance(data, dict)

    def test_top_level_keys(self, client):
        """Response must contain all required top-level keys."""
        data = client.get("/").json()
        required_keys = {"service", "system", "runtime", "request", "endpoints"}
        assert required_keys.issubset(data.keys())

    # ── service section ──

    def test_service_fields(self, client):
        """Service section must include name, version, description, framework."""
        service = client.get("/").json()["service"]
        for key in ("name", "version", "description", "framework"):
            assert key in service, f"Missing service field: {key}"
            assert isinstance(service[key], str)

    def test_service_name(self, client):
        """Service name should be 'devops-info-service'."""
        service = client.get("/").json()["service"]
        assert service["name"] == "devops-info-service"

    def test_service_framework(self, client):
        """Service framework should be 'FastAPI'."""
        service = client.get("/").json()["service"]
        assert service["framework"] == "FastAPI"

    # ── system section ──

    def test_system_fields(self, client):
        """System section must include hostname, platform, and other info."""
        system = client.get("/").json()["system"]
        required = (
            "hostname",
            "platform",
            "platform_version",
            "architecture",
            "cpu_count",
            "python_version",
        )
        for key in required:
            assert key in system, f"Missing system field: {key}"

    def test_system_hostname_is_string(self, client):
        """Hostname should be a non-empty string."""
        hostname = client.get("/").json()["system"]["hostname"]
        assert isinstance(hostname, str)
        assert len(hostname) > 0

    def test_system_cpu_count_is_positive_int(self, client):
        """CPU count should be a positive integer."""
        cpu = client.get("/").json()["system"]["cpu_count"]
        assert isinstance(cpu, int)
        assert cpu > 0

    # ── runtime section ──

    def test_runtime_fields(self, client):
        """Runtime section must include uptime and timing info."""
        runtime = client.get("/").json()["runtime"]
        required = (
            "uptime_seconds",
            "uptime_human",
            "current_time",
            "timezone",
        )
        for key in required:
            assert key in runtime, f"Missing runtime field: {key}"

    def test_runtime_uptime_is_non_negative(self, client):
        """Uptime seconds should be a non-negative integer."""
        uptime = client.get("/").json()["runtime"]["uptime_seconds"]
        assert isinstance(uptime, int)
        assert uptime >= 0

    def test_runtime_current_time_is_iso_format(self, client):
        """Current time should be a parseable ISO 8601 string."""
        from datetime import datetime

        current_time = client.get("/").json()["runtime"]["current_time"]
        # Should not raise
        datetime.fromisoformat(current_time)

    # ── request section ──

    def test_request_fields(self, client):
        """Request section must include client_ip, user_agent, method, path."""
        req = client.get("/").json()["request"]
        for key in ("client_ip", "user_agent", "method", "path"):
            assert key in req, f"Missing request field: {key}"

    def test_request_method_is_get(self, client):
        """Request method should reflect the actual HTTP method used."""
        req = client.get("/").json()["request"]
        assert req["method"] == "GET"

    def test_request_path_is_root(self, client):
        """Request path should be '/'."""
        req = client.get("/").json()["request"]
        assert req["path"] == "/"

    # ── endpoints section ──

    def test_endpoints_is_list(self, client):
        """Endpoints should be a non-empty list."""
        endpoints = client.get("/").json()["endpoints"]
        assert isinstance(endpoints, list)
        assert len(endpoints) >= 2

    def test_endpoints_contain_root_and_health(self, client):
        """Endpoints list should advertise / and /health."""
        endpoints = client.get("/").json()["endpoints"]
        paths = [ep["path"] for ep in endpoints]
        assert "/" in paths
        assert "/health" in paths


# ─── GET /health endpoint tests ─────────────────────────────────────


class TestHealthEndpoint:
    """Tests for the GET /health endpoint."""

    def test_returns_200(self, client):
        """Health endpoint should return HTTP 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_returns_json(self, client):
        """Health endpoint should return valid JSON."""
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"

    def test_required_fields(self, client):
        """Health response must contain status, timestamp, uptime_seconds."""
        data = client.get("/health").json()
        for key in ("status", "timestamp", "uptime_seconds"):
            assert key in data, f"Missing health field: {key}"

    def test_status_is_healthy(self, client):
        """Health status should be 'healthy'."""
        data = client.get("/health").json()
        assert data["status"] == "healthy"

    def test_uptime_is_non_negative_int(self, client):
        """Uptime seconds should be a non-negative integer."""
        uptime = client.get("/health").json()["uptime_seconds"]
        assert isinstance(uptime, int)
        assert uptime >= 0

    def test_timestamp_is_utc_iso(self, client):
        """Timestamp should be a valid ISO 8601 UTC datetime."""
        from datetime import datetime

        ts = client.get("/health").json()["timestamp"]
        parsed = datetime.fromisoformat(ts)
        assert parsed.tzinfo is not None  # should be timezone-aware


# ─── Error handling tests ────────────────────────────────────────────


class TestErrorHandling:
    """Tests for custom error handlers."""

    def test_404_on_unknown_route(self, client):
        """Non-existent routes should return HTTP 404."""
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_404_response_structure(self, client):
        """404 response should have error and message fields."""
        data = client.get("/nonexistent").json()
        assert "error" in data
        assert "message" in data

    def test_404_message_content(self, client):
        """404 message should indicate endpoint does not exist."""
        data = client.get("/nonexistent").json()
        assert "does not exist" in data["message"].lower()

    def test_method_not_allowed(self, client):
        """POST to GET-only endpoint should return 405."""
        response = client.post("/health")
        assert response.status_code == 405
