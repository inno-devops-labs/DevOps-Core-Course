import pytest
import pytz

from app import app, get_current_time
from datetime import datetime


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_get_current_time_format():
    time_str = get_current_time()
    try:
        datetime.strptime(time_str, "%H:%M:%S")
    except ValueError:
        pytest.fail("Unexpected time format! Expected format: %H:%M:%S")


def test_show_time_route(client):
    response = client.get("/")
    assert response.status_code == 200
    content = response.data.decode("utf-8")
    assert "MOSCOW TIME" in content
    assert '<div id="time-container">' in content
    assert '<p id="time">' in content


def test_api_time_route(client):
    response = client.get("/api/time/")
    assert response.status_code == 200
    json_data = response.get_json()
    assert "time" in json_data

    msk_tz = pytz.timezone("Europe/Moscow")
    current_time = datetime.now(msk_tz).strftime("%H:%M:%S")
    assert json_data["time"] == current_time
