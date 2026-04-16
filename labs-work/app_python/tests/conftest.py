"""Pytest configuration and fixtures for devops-info-service tests."""

import os

import pytest

import app as app_module
from app import app as flask_app


@pytest.fixture(autouse=True)
def _visits_dir(tmp_path, monkeypatch):
    """Set DATA_DIR to a temporary directory for every test."""
    data_dir = str(tmp_path / "data")
    monkeypatch.setattr(app_module, 'DATA_DIR', data_dir)
    monkeypatch.setattr(app_module, 'VISITS_FILE', os.path.join(data_dir, 'visits'))


@pytest.fixture
def app():
    """Create application for testing."""
    flask_app.config.update({
        'TESTING': True,
    })
    yield flask_app


@pytest.fixture
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test CLI runner."""
    return app.test_cli_runner()
