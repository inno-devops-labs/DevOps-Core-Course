import pytest
from app import app as flask_app, visit_counter


@pytest.fixture()
def client(tmp_path):
    visits_file = tmp_path / "visits"
    config_file = tmp_path / "config.json"
    config_file.write_text(
        """
{
  "applicationName": "devops-info-service",
  "environment": "test",
  "featureFlags": {
    "visitsPersistence": true
  },
  "settings": {
    "source": "pytest"
  }
}
""".strip()
    )
    flask_app.config.update(
        TESTING=True,
        APP_CONFIG_PATH=str(config_file),
    )
    visit_counter.reset(visits_file)
    with flask_app.test_client() as c:
        yield c
