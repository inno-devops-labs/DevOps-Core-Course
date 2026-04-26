# DevOps Info Service (Python)

[![Python CI](https://github.com/ellilin/DevOps/workflows/Python%20CI%20-%20DevOps%20Info%20Service/badge.svg)](https://github.com/ellilin/DevOps/actions/workflows/python-ci.yml)
[![codecov](https://codecov.io/gh/ellilin/DevOps/branch/master/graph/badge.svg?flag=python)](https://codecov.io/gh/ellilin/DevOps)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/release/python-3130/)
[![Flask](https://img.shields.io/badge/flask-3.1.0-green.svg)](https://flask.palletsprojects.com/)

A production-ready Python web service that provides comprehensive information about itself and its runtime environment.

## Overview

The DevOps Info Service is a RESTful API that returns detailed system information, health status, and service metadata. This service serves as a foundation for learning DevOps practices including containerization, CI/CD, monitoring, and orchestration.

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)

## Installation

1. Clone the repository and navigate to the app_python directory:
```bash
cd app_python
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:

On macOS/Linux:
```bash
source venv/bin/activate
```

On Windows:
```bash
venv\Scripts\activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

### Default Configuration
```bash
python app.py
```
The service will start on `http://0.0.0.0:8000`

### Custom Configuration
```bash
# Custom port
PORT=8080 python app.py

# Custom host and port
HOST=127.0.0.1 PORT=3000 python app.py

# Enable debug mode
DEBUG=True python app.py
```

## Running Tests

### Run All Tests
```bash
cd app_python
pytest tests/ -v
```

### Run Tests with Coverage
```bash
pytest --cov=. --cov-report=html --cov-report=term --verbose
```

### Run Specific Test
```bash
pytest tests/test_app.py::TestMainEndpoint::test_main_endpoint_returns_200
```

### View Coverage Report
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## API Endpoints

### GET /

Returns comprehensive service and system information. Each successful request to this
endpoint increments the persisted visits counter stored in `VISITS_FILE`.

**Response:**
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Flask"
  },
  "configuration": {
    "applicationName": "devops-info-service",
    "environment": "dev"
  },
  "visits": 42,
  "system": {
    "hostname": "my-laptop",
    "platform": "Linux",
    "platform_version": "Ubuntu 24.04",
    "architecture": "x86_64",
    "cpu_count": 8,
    "python_version": "3.13.1"
  },
  "runtime": {
    "uptime_seconds": 3600,
    "uptime_human": "1 hour, 0 minutes",
    "current_time": "2026-01-07T14:30:00.000Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/7.81.0",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/health", "method": "GET", "description": "Health check"},
    {"path": "/visits", "method": "GET", "description": "Current visit count"},
    {"path": "/config", "method": "GET", "description": "Current application config"},
    {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"}
  ]
}
```

### GET /health

Simple health check endpoint for monitoring and Kubernetes probes.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T14:30:00.000Z",
  "uptime_seconds": 3600
}
```

### GET /visits

Returns the current persisted root endpoint visit count without incrementing it.

**Response:**
```json
{
  "visits": 42,
  "file": "/data/visits"
}
```

### GET /config

Returns the current JSON configuration loaded from `CONFIG_FILE`. The application
checks the file modification time and reloads changed ConfigMap content without a
process restart when Kubernetes updates the mounted file.

**Response:**
```json
{
  "config": {
    "applicationName": "devops-info-service",
    "environment": "dev"
  },
  "file": "/config/config.json"
}
```

## Configuration

The application can be configured via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Host to bind the server to |
| `PORT` | `8000` | Port number for the server |
| `DEBUG` | `False` | Enable debug mode |
| `VISITS_FILE` | `/data/visits` | File used to persist root endpoint visit count |
| `CONFIG_FILE` | `/config/config.json` | JSON configuration file, usually mounted from a ConfigMap |

## Examples

### Testing with curl
```bash
# Main endpoint
curl http://localhost:8000/

# Health check
curl http://localhost:8000/health

# Current visits counter
curl http://localhost:8000/visits

# Current app configuration
curl http://localhost:8000/config

# Pretty print JSON
curl http://localhost:8000/ | jq
```

### Testing with Python
```bash
python -c "import requests; print(requests.get('http://localhost:8000/').json())"
```

## Docker

### Building the Image

To build the Docker image locally, navigate to the `app_python` directory and run:

```bash
docker build -t devops-info-service:latest .
```

For a more specific tag (recommended):

```bash
docker build -t <your-dockerhub-username>/devops-info-service:v1.0.0 .
```

### Running the Container

Run the container with port mapping to access the service:

```bash
# Run with default port mapping
docker run -d -p 8000:8000 --name devops-info devops-info-service:latest

# Run with custom environment variables
docker run -d -p 8080:8000 -e PORT=8000 --name devops-info devops-info-service:latest

# Run in the background and view logs
docker run -d -p 8000:8000 --name devops-info devops-info-service:latest
docker logs -f devops-info
```

### Running with Docker Compose and Persistent Visits

The Lab 12 Docker Compose file mounts `./data` to `/data`, so the visits counter
survives container restarts. It also mounts `./config/config.json` at
`/config/config.json` for local config reload testing.

```bash
cd app_python
docker compose up --build -d
curl http://localhost:8000/
curl http://localhost:8000/
curl http://localhost:8000/visits
cat data/visits
docker compose restart
curl http://localhost:8000/visits
docker compose down
```

### Pulling from Docker Hub

If the image is published to Docker Hub:

```bash
# Pull the latest version
docker pull <your-dockerhub-username>/devops-info-service:latest

# Pull a specific version
docker pull <your-dockerhub-username>/devops-info-service:v1.0.0

# Run the pulled image
docker run -d -p 8000:8000 <your-dockerhub-username>/devops-info-service:latest
```

### Docker Benefits

- **Portability**: Runs the same way on any system with Docker installed
- **Isolation**: No dependency conflicts with your local environment
- **Security**: Runs as non-root user with minimal attack surface
- **Consistency**: Same image from development to production

## Project Structure

```
app_python/
├── app.py                    # Main application
├── requirements.txt          # Dependencies
├── Dockerfile               # Docker image definition
├── .dockerignore            # Files to exclude from Docker build
├── .gitignore               # Git ignore
├── README.md                # This file
├── tests/                   # Unit tests
│   └── __init__.py
└── docs/                    # Lab documentation
    ├── LAB01.md            # Lab submission
    ├── LAB02.md            # Lab 2 documentation
    └── screenshots/        # Proof of work
```

## Best Practices Implemented

- Clean code organization with clear function names
- Proper imports grouping
- Error handling for 404 and 500 errors
- Structured logging
- PEP 8 compliant code
- Environment variable configuration
- Comprehensive documentation

## Future Enhancements

This service will evolve throughout the DevOps course:
- **Lab 2:** ✅ Containerization with Docker
- **Lab 3:** Unit tests and CI/CD pipeline
- **Lab 8:** Prometheus metrics endpoint
- **Lab 9:** Kubernetes deployment
- **Lab 12:** Persistent storage with visit counter
- **Lab 13:** GitOps with ArgoCD

## License

Educational use for DevOps course.
