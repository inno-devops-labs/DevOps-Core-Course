"""Pytest configuration - ensures app_python is on the import path."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
