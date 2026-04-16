import os

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"


def get_visits_file_path() -> str:
    """Path to the visits counter file (read on each access; supports tests with monkeypatched env)."""
    return os.getenv("VISITS_FILE_PATH", "/data/visits")
