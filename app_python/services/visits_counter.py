import os
import threading
from pathlib import Path

from config import get_visits_file_path

_lock = threading.Lock()


def _read_int(path: Path) -> int:
    try:
        text = path.read_text(encoding="utf-8").strip()
        return int(text) if text else 0
    except (FileNotFoundError, ValueError):
        return 0


def _atomic_write(path: Path, value: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(str(value), encoding="utf-8")
    os.replace(tmp, path)


def read_count() -> int:
    """Current visit count (does not increment)."""
    return _read_int(Path(get_visits_file_path()))


def increment() -> int:
    """Increment counter on root path access; returns new total."""
    path = Path(get_visits_file_path())
    with _lock:
        n = _read_int(path) + 1
        _atomic_write(path, n)
        return n
