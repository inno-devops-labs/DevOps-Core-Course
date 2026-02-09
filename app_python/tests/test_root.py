def test_root_status_code(client):
    r = client.get("/")
    assert r.status_code == 200


def test_root_json_structure_and_required_fields(client):
    r = client.get("/")
    data = r.json()

    for key in ["service", "system", "runtime", "request", "endpoints"]:
        assert key in data, f"Missing top-level field: {key}"

    service = data["service"]
    for key in ["name", "version", "description", "framework"]:
        assert key in service, f"Missing service field: {key}"
    assert service["name"] == "devops-info-service"
    assert service["framework"] == "FastAPI"

    system = data["system"]
    for key in [
        "hostname",
        "platform",
        "platform_version",
        "architecture",
        "cpu_count",
        "python_version",
    ]:
        assert key in system, f"Missing system field: {key}"

    assert isinstance(system["hostname"], str) and system["hostname"]
    assert isinstance(system["platform"], str) and system["platform"]
    assert isinstance(system["architecture"], str) and system["architecture"]
    assert ((system["cpu_count"] is None) or
            isinstance(system["cpu_count"], int))

    runtime = data["runtime"]
    for key in ["uptime_seconds", "uptime_human", "current_time", "timezone"]:
        assert key in runtime, f"Missing runtime field: {key}"

    assert isinstance(runtime["uptime_seconds"], int)
    assert runtime["uptime_seconds"] >= 0
    assert isinstance(runtime["uptime_human"], str) and runtime["uptime_human"]
    assert runtime["timezone"] == "UTC"

    assert isinstance(runtime["current_time"], str)
    assert "T" in runtime["current_time"]

    req = data["request"]
    for key in ["client_ip", "user_agent", "method", "path"]:
        assert key in req, f"Missing request field: {key}"

    assert req["method"] == "GET"
    assert req["path"] == "/"
    assert isinstance(req["client_ip"], str) and req["client_ip"]
    assert ("user_agent" in req)

    endpoints = data["endpoints"]
    assert isinstance(endpoints, list)
    assert len(endpoints) >= 2

    paths = {(e.get("path"), e.get("method")) for e in endpoints}
    assert ("/", "GET") in paths
    assert ("/health", "GET") in paths

    for e in endpoints:
        for key in ["path", "method", "description"]:
            assert key in e
        assert isinstance(e["path"], str) and e["path"].startswith("/")
        assert e["method"] in {"GET", "POST", "PUT", "DELETE", "PATCH"}
        assert isinstance(e["description"], str) and e["description"]
