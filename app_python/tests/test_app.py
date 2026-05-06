import re

from app_python.app import app, get_moscow_time


def test_get_moscow_time_format():
    result = get_moscow_time()

    assert re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", result)


def test_index_returns_success_status_code():
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200


def test_index_contains_expected_content():
    client = app.test_client()

    response = client.get("/")
    body = response.get_data(as_text=True)

    assert "Current time in Moscow" in body
    assert "Refresh the page to update the time." in body


def test_index_contains_time_value():
    client = app.test_client()

    response = client.get("/")
    body = response.get_data(as_text=True)

    assert re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", body)
