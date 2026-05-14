# DevOps Info Service

[![CI/CD Pipeline](https://github.com/pav0rkmert/DevOps-Core-Course/workflows/Python%20CI%2FCD%20Pipeline/badge.svg)](https://github.com/pav0rkmert/DevOps-Core-Course/actions)
[![Coverage](https://codecov.io/gh/pav0rkmert/DevOps-Core-Course/branch/main/graph/badge.svg)](https://codecov.io/gh/pav0rkmert/DevOps-Core-Course)

A Python web service that provides detailed information about itself and its runtime environment. This service is part of the DevOps course and will evolve throughout the labs to include containerization, CI/CD, monitoring, and persistence.

## Overview

The DevOps Info Service exposes REST API endpoints that return:
- Service metadata (name, version, framework)
- System information (hostname, platform, architecture, CPU count)
- Runtime information (uptime, current time)
- Request details (client IP, user agent)
- Deployment metadata (Fly app, region, secret presence)
- Persistent visit counter state
- Health status for monitoring and Kubernetes probes

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

## Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd app_python
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### Development Mode

```bash
python app.py
```

The service will start on `http://0.0.0.0:5000` by default.

### Custom Configuration

```bash
# Custom port
PORT=8080 python app.py

# Custom host and port
HOST=127.0.0.1 PORT=3000 python app.py

# Enable debug mode
DEBUG=true python app.py
```

### Production Mode (with Gunicorn)

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Docker

The application is containerized and available on Docker Hub.

### Building Locally

```bash
# Build the image
docker build -t devops-info-service .

# Run a container
docker run -d -p 5000:5000 --name devops-app devops-info-service

# Test it
curl http://localhost:5000/
curl http://localhost:5000/health

# Stop and remove
docker stop devops-app && docker rm devops-app
```

### Custom Configuration

```bash
# Run on a different port
docker run -d -p 8080:8080 -e PORT=8080 devops-info-service

# Run with debug mode
docker run -d -p 5000:5000 -e DEBUG=true devops-info-service
```

### Pulling from Docker Hub

```bash
# Pull the image
docker pull <your-dockerhub-username>/devops-info-service:latest

# Run from Docker Hub
docker run -d -p 5000:5000 <your-dockerhub-username>/devops-info-service:latest
```

### Docker Image Details

| Property | Value |
|----------|-------|
| Base Image | `python:3.13-slim` |
| User | Non-root (`appuser`, UID 1000) |
| Exposed Port | 5000 |
| Health Check | Built-in (`/health` endpoint) |

## API Endpoints

### `GET /` — Service Information

Returns comprehensive service and system information.

**Request:**
```bash
curl http://localhost:5000/
```

**Response:**
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
    "platform_version": "Darwin-25.2.0-...",
    "architecture": "arm64",
    "cpu_count": 8,
    "python_version": "3.11.0"
  },
  "runtime": {
    "uptime_seconds": 120,
    "uptime_human": "0 hours, 2 minutes",
    "current_time": "2026-01-28T12:00:00.000000+00:00",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/8.1.2",
    "method": "GET",
    "path": "/"
  },
  "deployment": {
    "platform": "local",
    "app_name": null,
    "region": null,
    "primary_region": null,
    "machine_id": null,
    "image_ref": null,
    "secrets": {
      "API_KEY": false,
      "DATABASE_URL": false
    }
  },
  "persistence": {
    "path": "/path/to/app_python/data/visits",
    "visits": 3
  },
  "endpoints": [
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/health", "method": "GET", "description": "Health check"},
    {"path": "/visits", "method": "GET", "description": "Persistent visit count"}
  ]
}
```

### `GET /health` — Health Check

Returns health status for monitoring and Kubernetes liveness/readiness probes.

**Request:**
```bash
curl http://localhost:5000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T12:00:00.000000+00:00",
  "uptime_seconds": 120
}
```

**HTTP Status:** `200 OK` when healthy.

### `GET /visits` — Persistent Visit Counter

Returns the current persisted counter without incrementing it.

```bash
curl http://localhost:5000/visits
```

```json
{
  "visits": 3,
  "storage": {
    "path": "/path/to/app_python/data/visits"
  }
}
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Host address to bind |
| `PORT` | `5000` | Port number |
| `DEBUG` | `False` | Enable Flask debug mode |
| `DATA_DIR` | `app_python/data` | Directory used for persisted visit counter |
| `VISITS_FILE` | `<DATA_DIR>/visits` | Override full path to visits counter file |
| `FLY_APP_NAME` | unset | Fly.io app name exposed in response metadata |
| `FLY_REGION` | unset | Current Fly.io region exposed in response metadata |
| `PRIMARY_REGION` | unset | Primary Fly.io region exposed in response metadata |
| `API_KEY` | unset | Secret presence exposed as boolean only |
| `DATABASE_URL` | unset | Secret presence exposed as boolean only |

## Project Structure

```
app_python/
├── app.py                    # Main application
├── requirements.txt          # Dependencies
├── pytest.ini               # Pytest configuration
├── Dockerfile               # Container definition
├── .dockerignore            # Docker build exclusions
├── .gitignore               # Git ignore rules
├── README.md                # This file
├── tests/                   # Unit tests
│   ├── __init__.py
│   └── test_app.py         # Test suite
└── docs/                    # Lab documentation
    ├── LAB01.md            # Lab 1 submission
    ├── LAB02.md            # Lab 2 submission
    ├── LAB03.md            # Lab 3 submission
    └── screenshots/        # Proof of work
```

## Testing

### Running Unit Tests

```bash
# Install test dependencies (if not already installed)
pip install -r requirements.txt

# Run all tests
pytest tests/

# Run tests with coverage report
pytest tests/ --cov=app --cov-report=term-missing

# Run tests with verbose output
pytest tests/ -v
```

### Test Coverage

The project uses `pytest-cov` for test coverage tracking. Coverage reports are automatically uploaded to Codecov on each CI run.

Current coverage target: **70%** (configured in `pytest.ini`)

### Manual Testing

```bash
# Test main endpoint
curl http://localhost:5000/ | jq

# Test health endpoint
curl http://localhost:5000/health | jq

# Test with custom headers
curl -A "TestAgent/1.0" http://localhost:5000/
```

### Test Structure

Tests are located in `tests/test_app.py` and cover:
- Main endpoint (`GET /`) - JSON structure, required fields, data types
- Health endpoint (`GET /health`) - Status, timestamp, uptime
- Error handling - 404 errors, invalid paths
- Helper functions - Service info, system info, endpoints list

## Development

### Code Style

This project follows PEP 8 style guidelines. Use a linter to check your code:

```bash
pip install flake8
flake8 app.py
```

### Logging

The application uses Python's built-in logging module. Logs include:
- Application startup information
- Request details (INFO level)
- Health checks (DEBUG level)
- Errors (WARNING/ERROR level)

## Future Enhancements

This service will evolve throughout the DevOps course:

- **Lab 2:** Docker containerization with multi-stage builds
- **Lab 3:** Unit tests and CI/CD pipeline
- **Lab 8:** Prometheus metrics endpoint (`/metrics`)
- **Lab 9:** Kubernetes deployment with health probes
- **Lab 12:** File persistence (`/visits` endpoint)
- **Lab 13:** Multi-environment GitOps deployment

## License

This project is part of the DevOps course curriculum.
