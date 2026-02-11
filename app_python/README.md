# DevOps Info Service

[![Python CI](https://github.com/karishka1222/DevOps-Core-Course/workflows/Python%20CI%2FCD/badge.svg?branch=lab3)](https://github.com/karishka1222/DevOps-Core-Course/actions/workflows/python-ci.yml)
[![codecov](https://codecov.io/gh/karishka1222/DevOps-Core-Course/branch/main/graph/badge.svg)](https://codecov.io/gh/karishka1222/DevOps-Core-Course)
![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)
![Flask](https://img.shields.io/badge/flask-3.1.0-green)

A Python web service that provides comprehensive information about itself and its runtime environment. This service reports system information, runtime metrics, and health status through a RESTful API.

## Overview

DevOps Info Service is a Flask-based web application designed to provide real-time information about:
- Service metadata (name, version, framework)
- System information (hostname, platform, CPU, Python version)
- Runtime metrics (uptime, current time)
- Request details (client IP, user agent, method, path)
- Health status for monitoring tools

This service serves as a foundation for DevOps practices and will evolve throughout the course to include containerization, CI/CD, monitoring, and persistence features.

## Prerequisites

- **Python:** 3.11 or higher
- **pip:** Python package manager
- **Operating System:** Linux, macOS, or Windows

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/karishka1222/DevOps-Core-Course.git
cd DevOps-Core-Course/app_python
```

### 2. Create Virtual Environment

It's recommended to use a virtual environment to isolate dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Running the Application

### Default Configuration

Run with default settings (host: 0.0.0.0, port: 5000):

```bash
python app.py
```

The service will be available at: `http://localhost:5000`

### Custom Configuration

Use environment variables to customize the service:

```bash
# Run on custom port
PORT=8080 python app.py

# Run on localhost only
HOST=127.0.0.1 PORT=3000 python app.py
```

## API Endpoints

### GET /

**Description:** Returns comprehensive service and system information

**Response:** JSON object containing:
- `service`: Service metadata (name, version, description, framework)
- `system`: System information (hostname, platform, architecture, CPU count, Python version)
- `runtime`: Runtime metrics (uptime, current time, timezone)
- `request`: Request details (client IP, user agent, method, path)
- `endpoints`: List of available API endpoints

**Example Request:**
```bash
curl http://localhost:5000/
```

**Example Response:**
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Flask"
  },
  "system": {
    "hostname": "my-laptop",
    "platform": "Darwin",
    "platform_version": "Darwin Kernel Version 25.2.0",
    "architecture": "arm64",
    "cpu_count": 8,
    "python_version": "3.13.1"
  },
  "runtime": {
    "uptime_seconds": 120,
    "uptime_human": "2 minutes",
    "current_time": "2026-01-27T14:30:00.000000+00:00",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/8.7.1",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {
      "path": "/",
      "method": "GET",
      "description": "Service information"
    },
    {
      "path": "/health",
      "method": "GET",
      "description": "Health check"
    }
  ]
}
```

### GET /health

**Description:** Health check endpoint for monitoring and orchestration tools (e.g., Kubernetes probes)

**Response:** JSON object with health status

**HTTP Status:** 200 OK (service is healthy)

**Example Request:**
```bash
curl http://localhost:5000/health
```

**Example Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-27T14:30:00.000000+00:00",
  "uptime_seconds": 120
}
```

## Configuration

The application can be configured using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Host address to bind (0.0.0.0 = all interfaces) |
| `PORT` | `5000` | Port number to listen on |
| `DEBUG` | `false` | Enable Flask debug mode (true/false) |


## Testing the Service

### Using curl

```bash
# Test main endpoint
curl http://localhost:5000/

# Test health endpoint
curl http://localhost:5000/health

# Pretty-print JSON output
curl http://localhost:5000/ | python -m json.tool
```

### Using Browser

Simply navigate to:
- Main endpoint: `http://localhost:5000/`
- Health check: `http://localhost:5000/health`

### Running Unit Tests

**Install Test Dependencies:**
```bash
pip install -r requirements-dev.txt
```

**Run Tests:**
```bash
# Run all tests
pytest

# Run with verbose output
pytest --verbose

# Run with coverage report
pytest --cov=. --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=. --cov-report=html
# Open htmlcov/index.html in browser
```

**Test Structure:**
- 20 comprehensive test cases
- 94% code coverage
- Tests for all endpoints, error handling, and edge cases
- Automated in CI/CD pipeline

## Project Structure

```
app_python/
├── app.py                  # Main application code
├── requirements.txt        # Python dependencies
├── requirements-dev.txt    # Development dependencies (testing, linting)
├── pytest.ini             # Pytest configuration
├── .gitignore             # Git ignore patterns
├── .dockerignore          # Docker ignore patterns
├── Dockerfile             # Docker image definition
├── README.md              # This file
├── tests/                 # Unit tests (Lab 3)
│   ├── __init__.py
│   └── test_app.py        # Test suite (20 test cases)
└── docs/                  # Lab documentation
    ├── LAB01.md           # Lab 1 submission
    ├── LAB02.md           # Lab 2 submission
    ├── LAB03.md           # Lab 3 submission (CI/CD)
    └── screenshots/       # Proof of work
```

## Dependencies

**Production Dependencies:**
- **Flask 3.1.0:** Web framework for building the API
- **Werkzeug 3.1.3:** WSGI utility library for Flask
- **requests 2.32.3:** HTTP library for making requests

**Development Dependencies:**
- **pytest 8.3.4:** Testing framework
- **pytest-cov 6.0.0:** Coverage plugin for pytest
- **pytest-flask 1.3.0:** Flask testing utilities
- **flake8 7.3.0:** Code linting and style checking
- **autopep8 2.3.2:** Automatic PEP 8 formatting

All dependencies are pinned to specific versions for reproducibility.

## Logging

The application uses Python's built-in logging module:

- **INFO level:** Startup messages, request information
- **DEBUG level:** Detailed health check logs
- **WARNING level:** 404 errors
- **ERROR level:** 500 errors and system info collection failures

Logs are output to console in the format:
```
YYYY-MM-DD HH:MM:SS - module - LEVEL - message
```

## Error Handling

The application handles common HTTP errors:

- **404 Not Found:** Returns JSON with error details
- **500 Internal Server Error:** Returns JSON with error message

All errors are logged for debugging purposes.

## Docker

The application is containerized and available as a Docker image.

### Building the Image

Build the Docker image locally:

```bash
docker build -t <your-username>/devops-python-app:latest .
```

### Running the Container

Run the container with port mapping:

```bash
docker run -d -p 5000:5000 --name devops-app <your-username>/devops-python-app:latest
```

Access the application at `http://localhost:5000/`

### Pulling from Docker Hub

Pull and run the pre-built image:

```bash
docker pull <your-username>/devops-python-app:latest
docker run -d -p 5000:5000 <your-username>/devops-python-app:latest
```

### Docker Commands

```bash
# View logs
docker logs devops-app

# Stop container
docker stop devops-app

# Remove container
docker rm devops-app

# View image details
docker inspect <your-username>/devops-python-app:latest
```

## Troubleshooting

### Port Already in Use

If you see "Address already in use" error:

```bash
# Use a different port
PORT=8080 python app.py

# Or for Docker:
docker run -d -p 8080:5000 <your-username>/devops-python-app:latest
```

### Module Not Found

If you see "ModuleNotFoundError":

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Docker Daemon Not Running

If you see "Cannot connect to the Docker daemon":

```bash
# Start Docker Desktop (macOS/Windows)
# Or start Docker daemon (Linux):
sudo systemctl start docker
```

## CI/CD Pipeline

This project uses GitHub Actions for continuous integration and deployment.

**Workflow Triggers:**
- Push to main/master/lab03 branches
- Pull requests to main/master
- Only when Python app files change (path filters)

**Pipeline Steps:**
1. **Test:** Install dependencies, lint with flake8, run pytest
2. **Security:** Scan dependencies with Snyk
3. **Build:** Build Docker image and push to Docker Hub

**Docker Images:**
- Latest builds available at: `karishka1222/devops-python-app`
- Tagged with CalVer: `latest` (on main/master) and `YYYY.MM.DD`

**View Workflow:** [GitHub Actions Tab](.github/workflows/python-ci.yml)

**Badges:**
- CI Status: Shows if tests are passing
- Coverage: Shows code coverage percentage
- Python Version: Python 3.11+ required
- Flask Version: Flask 3.1.0 used
