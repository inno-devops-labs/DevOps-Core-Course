Overview - What the service does
Prerequisites - Python version, dependencies
Installation
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
Running the Application
python app.py
# Or with custom config
PORT=8080 python app.py
API Endpoints
GET / - Service and system information
GET /health - Health check
Configuration - Environment variables table