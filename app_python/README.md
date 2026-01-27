# DevOps Info Service

## Overview
A simple Python web service that provides system, runtime, and request information.
Built as a foundation for DevOps monitoring tools.

## Prerequisites
- Python 3.11+
- pip

## Installation
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
## Running the Application
### Running the application
```bash
# run with default configuration (0.0.0.0:5000)
python app.py

# run with custom host and port
HOST=127.0.0.1 PORT=8080 DEBUG=True python app.py
```

* **HOST** - IP address to bind the server (default: `0.0.0.0`)
* **PORT** - Port number to run the application (default: `5000`)
* **DEBUG** - Enables debug mode with auto-reload (default: `False`)

## API Endpoints
   - `GET /` - Service and system information
   - `GET /health` - Health check
### Configuration

The application can be configured using environment variables:

| Variable | Default   | Description                                                 |
| -------- | --------- | ----------------------------------------------------------- |
| `HOST`   | `0.0.0.0` | IP address to bind the server                               |
| `PORT`   | `5000`    | Port number to run the application                          |
| `DEBUG`  | `False`   | Enable debug mode (auto-reload and detailed error messages) |
