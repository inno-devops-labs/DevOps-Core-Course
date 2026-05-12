"""Pytest configuration: visits file path and per-test file reset."""
from __future__ import annotations

import os
import tempfile

import pytest

_fd, _VISITS_TEST_PATH = tempfile.mkstemp(prefix="visits_", suffix=".txt")
os.close(_fd)
os.environ["VISITS_FILE_PATH"] = _VISITS_TEST_PATH


@pytest.fixture(autouse=True)
def _reset_visits_file():
    path = os.environ["VISITS_FILE_PATH"]
    if os.path.isfile(path):
        os.unlink(path)
    yield
