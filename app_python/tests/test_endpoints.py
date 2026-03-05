def test_root_ok_structure(client):
    r = client.get("/", headers={"User-Agent": "pytest"})
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data, dict)

    # required top-level keys
    for k in ("service", "system", "runtime", "request", "endpoints"):
        assert k in data

    # service
    assert data["service"]["name"] == "devops-info-service"
    assert data["service"]["version"] == "1.0.0"

    # system fields exist (values can vary)
    for k in (
        "hostname",
        "platform",
        "platform_version",
        "architecture",
        "cpu_count",
        "python_version",
    ):
        assert k in data["system"]

    # runtime
    assert isinstance(data["runtime"]["uptime_seconds"], int)
    assert "uptime_human" in data["runtime"]
    assert data["runtime"]["timezone"] == "UTC"

    # request echo
    assert data["request"]["path"] == "/"
    assert data["request"]["method"] == "GET"
    assert data["request"]["user_agent"] == "pytest"


def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    data = r.get_json()
    assert data["status"] == "healthy"
    assert isinstance(data["uptime_seconds"], int)
    assert "timestamp" in data


def test_404_json(client):
    r = client.get("/nope")
    assert r.status_code == 404
    data = r.get_json()
    assert data["error"] == "Not Found"


def test_client_ip_from_xff(client):
    r = client.get("/", headers={"X-Forwarded-For": "1.2.3.4, 10.0.0.1"})
    assert r.status_code == 200
    data = r.get_json()
    assert data["request"]["client_ip"] == "1.2.3.4"
