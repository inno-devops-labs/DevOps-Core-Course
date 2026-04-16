"""
Test configuration and fixtures for the DevOps Info Service
"""
import json

import pytest
from fastapi.testclient import TestClient

import app as app_module


@pytest.fixture
def client(tmp_path, monkeypatch):
    """
    Fixture that provides a TestClient for making requests to the FastAPI application.
    This allows testing endpoints without starting an actual server.
    """
    visits_file = tmp_path / "data" / "visits"
    config_file = tmp_path / "config" / "config.json"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text(
        json.dumps(
            {
                "applicationName": "devops-info-service",
                "environment": "test",
                "features": {
                    "visits": True,
                    "configHotReload": True,
                },
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("VISITS_FILE", str(visits_file))
    monkeypatch.setenv("APP_CONFIG_PATH", str(config_file))
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("LOG_LEVEL", "debug")
    monkeypatch.setenv("APP_DISPLAY_NAME", "DevOps Info Service Test")
    monkeypatch.setenv("FEATURE_VISITS_ENABLED", "true")
    monkeypatch.setenv("FEATURE_CONFIG_HOT_RELOAD", "true")
    app_module.configure_runtime()

    with TestClient(app_module.app) as test_client:
        yield test_client
