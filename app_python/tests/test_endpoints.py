def test_get_root_returns_expected_structure(client):
    resp = client.get("/", headers={"User-Agent": "pytest"})
    assert resp.status_code == 200
    assert resp.is_json

    data = resp.get_json()
    assert set(data.keys()) == {"service", "system", "runtime", "request", "endpoints"}

    assert data["service"]["name"] == "devops-info-service"
    assert data["service"]["framework"] == "Flask"

    assert isinstance(data["system"]["hostname"], str) and data["system"]["hostname"]
    assert (
        isinstance(data["system"]["cpu_count"], int)
        and data["system"]["cpu_count"] >= 0
    )

    assert (
        isinstance(data["runtime"]["uptime_seconds"], int)
        and data["runtime"]["uptime_seconds"] >= 0
    )
    assert isinstance(data["runtime"]["current_time"], str) and data["runtime"][
        "current_time"
    ].endswith("Z")

    assert data["request"]["method"] == "GET"
    assert data["request"]["path"] == "/"
    assert data["request"]["user_agent"] == "pytest"

    assert {"path": "/", "method": "GET", "description": "Service information"} in data[
        "endpoints"
    ]
    assert {"path": "/health", "method": "GET", "description": "Health check"} in data[
        "endpoints"
    ]


def test_get_health_returns_healthy(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.is_json

    data = resp.get_json()
    assert data["status"] == "healthy"
    assert isinstance(data["uptime_seconds"], int) and data["uptime_seconds"] >= 0
    assert isinstance(data["timestamp"], str) and data["timestamp"].endswith("Z")


def test_visits_counter_increments(client):
    first = client.get("/").get_json()
    second = client.get("/").get_json()

    assert first["request"]["path"] == "/"
    assert second["request"]["path"] == "/"

    visits = client.get("/visits")
    assert visits.status_code == 200
    assert visits.get_json() == {"visits": 2}


def test_unknown_endpoint_returns_json_404(client):
    resp = client.get("/does-not-exist")
    assert resp.status_code == 404
    assert resp.is_json
    data = resp.get_json()
    assert data == {"error": "Not Found", "message": "Endpoint does not exist"}


def test_root_can_return_json_500_when_dependency_fails(client, monkeypatch):
    import app as app_module

    def boom():
        raise RuntimeError("boom")

    monkeypatch.setattr(app_module, "get_system_info", boom)

    resp = client.get("/")
    assert resp.status_code == 500
    assert resp.is_json
    data = resp.get_json()
    assert data == {
        "error": "Internal Server Error",
        "message": "An unexpected error occurred",
    }
