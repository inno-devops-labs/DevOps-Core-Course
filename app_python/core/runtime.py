from datetime import datetime

START_TIME = None

def set_start_time():
    global START_TIME
    START_TIME = datetime.now()


def get_uptime() -> dict[str, str]:
    if START_TIME is None:
        raise RuntimeError("START_TIME is not initialized")

    delta = datetime.now() - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        'seconds': seconds,
        'human': f"{hours} hours, {minutes} minutes"
    }