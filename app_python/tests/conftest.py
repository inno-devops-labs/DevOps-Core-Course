
import pytest
import tempfile
import os
from app_python.app import app

@pytest.fixture
def client():
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.close()
    os.environ['VISITS_FILE'] = temp_file.name
    
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client
    
    try:
        os.unlink(temp_file.name)
    except:
        pass
