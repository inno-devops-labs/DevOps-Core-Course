
import pytest
import tempfile
import os

_temp_visits_file = tempfile.NamedTemporaryFile(delete=False)
_temp_visits_file.close()
os.environ['VISITS_FILE'] = _temp_visits_file.name

from app_python.app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client
    
    try:
        os.unlink(_temp_visits_file.name)
    except OSError:
        pass
