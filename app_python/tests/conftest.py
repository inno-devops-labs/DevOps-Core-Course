"""Pytest fixtures for DevOps Info Service tests."""

import os
import tempfile

import pytest

# Set before importing app — startup code reads the counter path at import time.
_test_visits_dir = tempfile.mkdtemp(prefix="visits_lab12_test_")
os.environ["VISITS_DATA_PATH"] = os.path.join(_test_visits_dir, "visits")

from app import app  # noqa: E402


@pytest.fixture
def client():
    """Create a Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c
