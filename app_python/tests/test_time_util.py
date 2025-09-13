import re
from unittest.mock import patch
from datetime import datetime
import pytest
import pytz
from utils.time_util import get_current_time_in_moscow


@pytest.fixture
def fixed_moscow_time():
    """Returns a fixed Moscow time for testing."""
    fixed_utc_time = datetime(2025, 2, 2, 12, 0, 0, tzinfo=pytz.utc)
    moscow_tz = pytz.timezone("Europe/Moscow")
    return fixed_utc_time.astimezone(moscow_tz).strftime("%Y-%m-%d %H:%M:%S")


@patch("utils.time_util.datetime")
def test_get_current_time_in_moscow(mock_datetime, fixed_moscow_time):
    """Test that get_current_time_in_moscow returns the correct Moscow time."""
    moscow_tz = pytz.timezone("Europe/Moscow")
    mock_datetime.now.return_value = datetime(2025, 2, 2, 15, 0, 0, tzinfo=moscow_tz)
    mock_datetime.strftime = datetime.strftime

    assert get_current_time_in_moscow() == fixed_moscow_time


def test_output_format():
    """Test that the function returns time in the correct format."""
    result = get_current_time_in_moscow()
    assert isinstance(result, str)
    assert re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", result)
