import os
import subprocess
import sys
import time

import requests


PORT = int(os.environ.get("PORT", "5000"))
BASE_URL = os.environ.get("BASE_URL", f"http://127.0.0.1:{PORT}")


def _start_server():
    # FastAPI app is defined in app_python/app.py as "app"
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(PORT),
    ]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def _wait_ready(timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{BASE_URL}/health", timeout=0.5)
            if r.status_code < 500:
                return True
        except Exception:
            pass
        time.sleep(0.3)
    return False


def test_root_ok_and_required_fields():
    p = _start_server()
    try:
        assert _wait_ready(), "Server did not become ready. Check how your app is started."

        r = requests.get(f"{BASE_URL}/", timeout=2)
        assert r.status_code == 200

        data = r.json()
        assert isinstance(data, dict), "Root endpoint must return a JSON object"

        # Top-level required keys
        for key in ("service", "system", "runtime", "request", "endpoints"):
            assert key in data, f"Root JSON must contain '{key}'"

        # service block required fields
        service = data["service"]
        assert isinstance(service, dict)
        for key in ("name", "version", "description", "framework"):
            assert key in service, f"service must contain '{key}'"
            assert isinstance(service[key], str) and service[key], f"service.{key} must be a non-empty string"

        assert service["framework"] == "FastAPI"

        # endpoints must be a non-empty list of objects with path+method
        endpoints = data["endpoints"]
        assert isinstance(endpoints, list) and len(endpoints) >= 2
        for ep in endpoints:
            assert isinstance(ep, dict)
            assert "path" in ep and isinstance(ep["path"], str)
            assert "method" in ep and isinstance(ep["method"], str)

        # Must contain our required endpoints
        paths = {(ep.get("path"), ep.get("method")) for ep in endpoints}
        assert ("/", "GET") in paths
        assert ("/health", "GET") in paths

        # runtime must contain uptime_seconds
        runtime = data["runtime"]
        assert isinstance(runtime, dict)
        assert "uptime_seconds" in runtime
        assert isinstance(runtime["uptime_seconds"], (int, float))
        assert runtime["uptime_seconds"] >= 0
    finally:
        p.terminate()
        p.wait(timeout=5)


def test_health_ok_and_structure():
    p = _start_server()
    try:
        assert _wait_ready(), "Server did not become ready. Check how your app is started."

        r = requests.get(f"{BASE_URL}/health", timeout=2)
        assert r.status_code == 200

        data = r.json()
        assert isinstance(data, dict), "Health endpoint must return a JSON object"

        # Required fields
        assert data.get("status") == "healthy"
        assert "timestamp" in data and isinstance(data["timestamp"], str) and data["timestamp"]
        assert "uptime_seconds" in data and isinstance(data["uptime_seconds"], (int, float))
        assert data["uptime_seconds"] >= 0
    finally:
        p.terminate()
        p.wait(timeout=5)


def test_error_case_not_found():
    p = _start_server()
    try:
        assert _wait_ready(), "Server did not become ready. Check how your app is started."

        r = requests.get(f"{BASE_URL}/nope", timeout=2)
        assert r.status_code == 404
    finally:
        p.terminate()
        p.wait(timeout=5)
