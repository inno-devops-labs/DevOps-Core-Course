"""
Unit tests for DevOps Info Service.
Tests all endpoints, response structure, and error handling.
"""
import json
import re

import pytest
from fastapi.testclient import TestClient

import app as app_module


@pytest.fixture
def app_state(tmp_path, monkeypatch):
    """Create an isolated test client and writable app state."""
    visits_file = tmp_path / "data" / "visits"
    config_path = tmp_path / "config" / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(
            {
                "application": {
                    "name": "devops-info-service-test",
                    "environment": "test",
                    "featureFlags": {
                        "visitsCounter": True,
                        "hotReload": True,
                    },
                },
                "settings": {
                    "responseMode": "detailed",
                    "storagePath": str(visits_file),
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(app_module, "CONFIG_PATH", str(config_path))
    monkeypatch.setattr(app_module, "VISITS_FILE", str(visits_file))
    monkeypatch.setattr(
        app_module,
        "VISIT_COUNTER",
        app_module.VisitCounterStore(str(visits_file)),
    )

    with TestClient(app_module.app) as client:
        yield {
            "client": client,
            "visits_file": visits_file,
            "config_path": config_path,
        }


@pytest.fixture
def client(app_state):
    """Expose the configured TestClient."""
    return app_state["client"]


def assert_metric_line_with_labels(metrics_text, metric_name, labels):
    """Assert one metric line contains the expected labels."""
    metric_pattern = re.compile(
        rf"^{re.escape(metric_name)}\{{.*\}}",
        re.MULTILINE,
    )

    for match in metric_pattern.finditer(metrics_text):
        line = match.group(0)
        if all(f'{key}="{value}"' in line for key, value in labels.items()):
            return

    label_summary = ", ".join(
        f'{key}="{value}"'
        for key, value in labels.items()
    )
    raise AssertionError(
        f"Metric {metric_name} with labels {{{label_summary}}} not found"
    )


# ---------------------------------------------------------------------------
# GET / — Main endpoint tests
# ---------------------------------------------------------------------------

class TestMainEndpoint:
    """Tests for the main endpoint GET /."""

    def test_status_code(self, client):
        """GET / should return 200 OK."""
        response = client.get("/")
        assert response.status_code == 200

    def test_response_is_json(self, client):
        """GET / should return valid JSON."""
        response = client.get("/")
        assert response.headers["content-type"] == "application/json"
        data = response.json()
        assert isinstance(data, dict)

    def test_top_level_keys(self, client):
        """Response must contain all required top-level keys."""
        data = client.get("/").json()
        required_keys = {
            "service",
            "system",
            "runtime",
            "request",
            "configuration",
            "visits",
            "endpoints",
        }
        assert required_keys.issubset(data.keys())

    # -- service section ---------------------------------------------------

    def test_service_fields(self, client):
        """Service section must contain the expected metadata fields."""
        service = client.get("/").json()["service"]
        for field in ("name", "version", "description", "framework"):
            assert field in service
            assert isinstance(service[field], str)
            assert len(service[field]) > 0

    def test_service_values(self, client):
        """Service section values must match constants."""
        service = client.get("/").json()["service"]
        assert service["name"] == app_module.SERVICE_INFO["name"]
        assert service["version"] == app_module.SERVICE_INFO["version"]
        assert service["framework"] == "FastAPI"

    # -- system section ----------------------------------------------------

    def test_system_fields(self, client):
        """System section must contain all required fields."""
        system = client.get("/").json()["system"]
        required = {
            "hostname", "platform", "platform_version",
            "architecture", "cpu_count", "python_version",
        }
        assert required.issubset(system.keys())

    def test_system_types(self, client):
        """System field types must be correct."""
        system = client.get("/").json()["system"]
        assert isinstance(system["hostname"], str)
        assert isinstance(system["platform"], str)
        assert isinstance(system["cpu_count"], int)
        assert system["cpu_count"] > 0

    # -- runtime section ---------------------------------------------------

    def test_runtime_fields(self, client):
        """Runtime section must contain uptime and time info."""
        runtime = client.get("/").json()["runtime"]
        for field in (
            "uptime_seconds",
            "uptime_human",
            "current_time",
            "timezone",
        ):
            assert field in runtime

    def test_runtime_uptime_nonnegative(self, client):
        """Uptime must be a non-negative integer."""
        uptime = client.get("/").json()["runtime"]["uptime_seconds"]
        assert isinstance(uptime, int)
        assert uptime >= 0

    def test_runtime_timezone_utc(self, client):
        """Timezone must be UTC."""
        assert client.get("/").json()["runtime"]["timezone"] == "UTC"

    # -- request section ---------------------------------------------------

    def test_request_fields(self, client):
        """Request section must contain ip, user-agent, method, path."""
        req = client.get("/").json()["request"]
        for field in ("client_ip", "user_agent", "method", "path"):
            assert field in req

    def test_request_method_is_get(self, client):
        """Request method must be GET."""
        assert client.get("/").json()["request"]["method"] == "GET"

    def test_request_path_is_root(self, client):
        """Request path must be /."""
        assert client.get("/").json()["request"]["path"] == "/"

    # -- endpoints section -------------------------------------------------

    def test_endpoints_list(self, client):
        """Endpoints must be a non-empty list."""
        eps = client.get("/").json()["endpoints"]
        assert isinstance(eps, list)
        assert len(eps) >= 4

    def test_endpoints_structure(self, client):
        """Each endpoint entry must have path, method, description."""
        for ep in client.get("/").json()["endpoints"]:
            assert "path" in ep
            assert "method" in ep
            assert "description" in ep

    def test_configuration_section(self, client):
        """Configuration section should expose file and environment data."""
        config = client.get("/").json()["configuration"]
        assert config["file"]["loaded"] is True
        assert config["file"]["data"]["application"]["environment"] == "test"
        assert config["environment"]["app_env"] == app_module.APP_ENV
        assert config["platform"]["provider"] in {"local", "fly.io"}
        assert config["secrets"]["APP_USERNAME"] is False
        assert config["secrets"]["APP_PASSWORD"] is False
        assert config["paths"]["config"] == app_module.CONFIG_PATH

    def test_configuration_reports_secret_presence(
        self,
        client,
        monkeypatch,
    ):
        """Tracked secrets should be reported as present without values."""
        monkeypatch.setenv("APP_USERNAME", "demo-user")
        monkeypatch.setenv("APP_PASSWORD", "demo-pass")

        config = client.get("/").json()["configuration"]
        assert config["secrets"]["APP_USERNAME"] is True
        assert config["secrets"]["APP_PASSWORD"] is True

    def test_root_endpoint_increments_visits(self, client, app_state):
        """GET / should increment the persisted visits counter."""
        first = client.get("/").json()["visits"]["count"]
        second = client.get("/").json()["visits"]["count"]

        assert first == 1
        assert second == 2
        assert (
            app_state["visits_file"].read_text(encoding="utf-8").strip() == "2"
        )


class TestVisitsEndpoint:
    """Tests for the persistent visits endpoint GET /visits."""

    def test_status_code(self, client):
        """GET /visits should return 200 OK."""
        assert client.get("/visits").status_code == 200

    def test_returns_current_count_without_incrementing(self, client):
        """GET /visits should not increment the counter."""
        client.get("/")
        current = client.get("/visits").json()["count"]
        again = client.get("/visits").json()["count"]

        assert current == 1
        assert again == 1

    def test_counter_persists_when_store_reloads(
        self,
        client,
        app_state,
        monkeypatch,
    ):
        """The visits file should restore the counter after reload."""
        client.get("/")
        client.get("/")

        reloaded_store = app_module.VisitCounterStore(
            str(app_state["visits_file"])
        )
        monkeypatch.setattr(app_module, "VISIT_COUNTER", reloaded_store)

        assert client.get("/visits").json()["count"] == 2

    def test_config_file_hot_reload(self, client, app_state):
        """The app should re-read the config file on each request."""
        updated_config = {
            "application": {
                "name": "devops-info-service-test",
                "environment": "reloaded",
                "featureFlags": {
                    "visitsCounter": True,
                    "hotReload": True,
                },
            },
            "settings": {
                "responseMode": "compact",
                "storagePath": str(app_state["visits_file"]),
            },
        }
        app_state["config_path"].write_text(
            json.dumps(updated_config),
            encoding="utf-8",
        )

        payload = client.get("/").json()
        assert (
            payload["configuration"]["file"]["data"]["application"][
                "environment"
            ]
            == "reloaded"
        )


# ---------------------------------------------------------------------------
# GET /health — Health check tests
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    """Tests for the health check endpoint GET /health."""

    def test_status_code(self, client):
        """GET /health should return 200 OK."""
        assert client.get("/health").status_code == 200

    def test_healthy_status(self, client):
        """Health status must be 'healthy'."""
        assert client.get("/health").json()["status"] == "healthy"

    def test_required_fields(self, client):
        """Health response must contain status, timestamp, uptime_seconds."""
        data = client.get("/health").json()
        for field in ("status", "timestamp", "uptime_seconds"):
            assert field in data

    def test_uptime_nonnegative(self, client):
        """Uptime seconds must be non-negative."""
        uptime = client.get("/health").json()["uptime_seconds"]
        assert isinstance(uptime, int)
        assert uptime >= 0

    def test_timestamp_format(self, client):
        """Timestamp must be a valid ISO 8601 string."""
        from datetime import datetime
        ts = client.get("/health").json()["timestamp"]
        # Should not raise
        datetime.fromisoformat(ts)


class TestReadinessEndpoint:
    """Tests for the readiness endpoint GET /ready."""

    def test_status_code(self, client):
        """GET /ready should return 200 OK."""
        assert client.get("/ready").status_code == 200

    def test_ready_status(self, client):
        """Readiness status must be 'ready'."""
        assert client.get("/ready").json()["status"] == "ready"

    def test_required_fields(self, client):
        """Readiness response must contain status and timestamp."""
        data = client.get("/ready").json()
        for field in ("status", "timestamp"):
            assert field in data


class TestMetricsEndpoint:
    """Tests for the Prometheus metrics endpoint GET /metrics."""

    def test_status_code(self, client):
        """GET /metrics should return 200 OK."""
        assert client.get("/metrics").status_code == 200

    def test_response_is_prometheus_text(self, client):
        """GET /metrics should return Prometheus text exposition format."""
        response = client.get("/metrics")
        assert response.headers["content-type"].startswith("text/plain")

    def test_expected_metric_series_exist(self, client):
        """Metrics output must include HTTP and app-specific metrics."""
        client.get("/")
        client.get("/visits")
        client.get("/health")
        client.get("/ready")
        client.get("/missing")

        metrics_text = client.get("/metrics").text
        assert "http_requests_total" in metrics_text
        assert "http_request_duration_seconds" in metrics_text
        assert "http_requests_in_progress" in metrics_text
        assert "devops_info_endpoint_calls_total" in metrics_text
        assert "devops_info_system_info_collection_seconds" in metrics_text

    def test_metrics_include_expected_labels(self, client):
        """Metrics should expose normalized labels for success and 404s."""
        client.get("/")
        client.get("/visits")
        client.get("/health")
        client.get("/ready")
        client.get("/missing")

        metrics_text = client.get("/metrics").text
        assert_metric_line_with_labels(
            metrics_text,
            "http_requests_total",
            {"method": "GET", "endpoint": "/", "status_code": "200"},
        )
        assert_metric_line_with_labels(
            metrics_text,
            "http_requests_total",
            {"method": "GET", "endpoint": "/health", "status_code": "200"},
        )
        assert_metric_line_with_labels(
            metrics_text,
            "http_requests_total",
            {"method": "GET", "endpoint": "/visits", "status_code": "200"},
        )
        assert_metric_line_with_labels(
            metrics_text,
            "http_requests_total",
            {"method": "GET", "endpoint": "/ready", "status_code": "200"},
        )
        assert_metric_line_with_labels(
            metrics_text,
            "http_requests_total",
            {"method": "GET", "endpoint": "/unknown", "status_code": "404"},
        )
        assert_metric_line_with_labels(
            metrics_text,
            "devops_info_endpoint_calls_total",
            {"endpoint": "/"},
        )
        assert_metric_line_with_labels(
            metrics_text,
            "devops_info_endpoint_calls_total",
            {"endpoint": "/health"},
        )
        assert_metric_line_with_labels(
            metrics_text,
            "devops_info_endpoint_calls_total",
            {"endpoint": "/visits"},
        )
        assert_metric_line_with_labels(
            metrics_text,
            "devops_info_endpoint_calls_total",
            {"endpoint": "/ready"},
        )


# ---------------------------------------------------------------------------
# Error handling tests
# ---------------------------------------------------------------------------

class TestErrorHandling:
    """Tests for error handling (404)."""

    def test_404_status_code(self, client):
        """Non-existent route should return 404."""
        assert client.get("/nonexistent").status_code == 404

    def test_404_json_body(self, client):
        """404 response must contain error and message fields."""
        data = client.get("/nonexistent").json()
        assert "error" in data
        assert "message" in data

    def test_404_includes_path(self, client):
        """404 response must include the requested path."""
        data = client.get("/some/bad/path").json()
        assert data["path"] == "/some/bad/path"


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------

class TestHelpers:
    """Tests for helper / utility functions."""

    def test_get_uptime_structure(self):
        """get_uptime must return dict with seconds and human keys."""
        result = app_module.get_uptime()
        assert "seconds" in result
        assert "human" in result
        assert isinstance(result["seconds"], int)
        assert isinstance(result["human"], str)

    def test_get_system_info_keys(self):
        """get_system_info must return all expected keys."""
        info = app_module.get_system_info()
        expected = {
            "hostname", "platform", "platform_version",
            "architecture", "cpu_count", "python_version",
        }
        assert expected.issubset(info.keys())

    def test_start_time_exists(self):
        """START_TIME must be set."""
        assert app_module.START_TIME is not None
