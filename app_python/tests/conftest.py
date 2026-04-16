
import pytest
import tempfile
import os

@pytest.fixture
def client():
    # Create temp file for visits
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.close()
    os.environ['VISITS_FILE'] = temp_file.name
    
    # Import app after setting env var
    from app_python.app import app
    
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client
    
    # Clean up
    try:
        os.unlink(temp_file.name)
    except OSError:
        pass
