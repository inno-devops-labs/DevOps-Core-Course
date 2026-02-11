from datetime import datetime, timezone
from typing import TypedDict

START_TIME = datetime.now(timezone.utc)


class UptimeInfo(TypedDict):
    seconds: int
    human: str


def get_uptime() -> UptimeInfo:
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        "seconds": seconds,
        "human": f"{hours} hours, {minutes} minutes",
    }
