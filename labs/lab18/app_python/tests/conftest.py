import pytest
import tempfile
import os

@pytest.fixture
def client():
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.close()
    os.environ['VISITS_FILE'] = temp_file.name
    
    from app_python.app import app
    
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client
    
    try:
        os.unlink(temp_file.name)
    except OSError:
        pass