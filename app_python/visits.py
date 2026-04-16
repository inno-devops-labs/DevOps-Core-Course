import os
import threading
from pathlib import Path

DATA_DIR = os.getenv("DATA_DIR", "/data")
VISITS_FILE = os.path.join(DATA_DIR, "visits")

_lock = threading.Lock()


def _ensure_data_dir():
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)


def read_visits() -> int:
    try:
        with open(VISITS_FILE, "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0


def increment_visits() -> int:
    with _lock:
        count = read_visits() + 1
        _ensure_data_dir()
        tmp = VISITS_FILE + ".tmp"
        with open(tmp, "w") as f:
            f.write(str(count))
        os.replace(tmp, VISITS_FILE)
        return count
