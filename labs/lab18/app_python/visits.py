import os
import threading
from pathlib import Path

_lock = threading.Lock()


def _data_dir() -> str:
    return os.getenv("DATA_DIR", "/data")


def _visits_file() -> str:
    return os.path.join(_data_dir(), "visits")


def _ensure_data_dir():
    Path(_data_dir()).mkdir(parents=True, exist_ok=True)


def read_visits() -> int:
    try:
        with open(_visits_file(), "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0


def increment_visits() -> int:
    with _lock:
        count = read_visits() + 1
        _ensure_data_dir()
        vf = _visits_file()
        tmp = vf + ".tmp"
        with open(tmp, "w") as f:
            f.write(str(count))
        os.replace(tmp, vf)
        return count
