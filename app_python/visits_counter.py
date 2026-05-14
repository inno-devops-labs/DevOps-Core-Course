import os
import threading

VISITS_FILE = os.getenv("VISITS_FILE", "/data/visits")

_lock = threading.Lock()


def _read_count() -> int:
    try:
        with open(VISITS_FILE, "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0


def _write_count(count: int) -> None:
    os.makedirs(os.path.dirname(VISITS_FILE), exist_ok=True)
    tmp = VISITS_FILE + ".tmp"
    with open(tmp, "w") as f:
        f.write(str(count))
    os.replace(tmp, VISITS_FILE)


def increment() -> int:
    with _lock:
        count = _read_count() + 1
        _write_count(count)
        return count


def get_count() -> int:
    with _lock:
        return _read_count()
