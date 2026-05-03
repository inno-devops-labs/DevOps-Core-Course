import pytest
import app as app_module


@pytest.fixture
def client():
    """
    Creates a Flask test client for each test.
    """
    app_module.app.config["TESTING"] = True
    app_module.VISITS_FILE = "/tmp/devops-core-course-test-visits"
    app_module._write_visits_count(0)

    with app_module.app.test_client() as client:
        yield client
