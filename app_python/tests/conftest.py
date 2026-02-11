import os
import sys

# add app_python/ to import path so "import app" works
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
