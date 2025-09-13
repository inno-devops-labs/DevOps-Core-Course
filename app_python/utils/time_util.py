from datetime import datetime
import pytz


def get_current_time_in_moscow():
    """Get the current time in Moscow."""
    moscow_tz = pytz.timezone("Europe/Moscow")
    return datetime.now(moscow_tz).strftime("%Y-%m-%d %H:%M:%S")
