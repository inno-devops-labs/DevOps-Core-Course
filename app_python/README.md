# DevOps Info Service - Python

[![Python CI](https://github.com/Arino4kaMyr/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)](https://github.com/Arino4kaMyr/DevOps-Core-Course/actions/workflows/python-ci.yml)
[![codecov](https://codecov.io/github/Arino4kaMyr/DevOps-Core-Course/graph/badge.svg?flag=python)](https://codecov.io/github/Arino4kaMyr/DevOps-Core-Course?flag=python)

A production-ready web service that provides comprehensive information about itself and its runtime environment. Built with Flask framework.

## Overview

The DevOps Info Service is a RESTful API that exposes system information, runtime metrics, and health status. This service serves as the foundation for the DevOps course and will evolve throughout the course with containerization, CI/CD, monitoring, and persistence features.

**Key Features:**
- System information endpoint (`GET /`)
- Health check endpoint (`GET /health`)
- Configurable via environment variables
- Production-ready error handling and logging

## Prerequisites

- **Python:** 3.11 or higher
- **pip:** Python package manager
- **Virtual environment:** Recommended for dependency isolation

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd DevOps-Core-Course/app_python
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   ```bash
   # On macOS/Linux:
   source venv/bin/activate
   
   # On Windows:
   venv\Scripts\activate
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### Basic Usage

Run the application with default settings (host: `0.0.0.0`, port: `5001`):

```bash
python app.py
```

### Custom Configuration

Configure the application using environment variables:

```bash
# Custom port
PORT=8080 python app.py

# Custom host and port
HOST=127.0.0.1 PORT=3000 python app.py

# Enable debug mode
DEBUG=true python app.py
```

The service will be available at `http://<HOST>:<PORT>`

## API Endpoints

### `GET /`

Returns comprehensive service and system information.

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
    "platform_version": "25.2.0",
    "architecture": "arm64",
    "cpu_count": 8,
    "python_version": "3.13.1"
  },
  "runtime": {
    "uptime_seconds": 3600.5,
    "uptime_human": "1 hour, 0 minutes, 0 seconds",
    "current_time": "2026-01-31T17:30:00.000Z",
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
    {"path": "/health", "method": "GET", "description": "Health check"}
  ]
}
```

**Example Request:**
```bash
curl http://localhost:5001/
```

### `GET /health`

Simple health check endpoint for monitoring and Kubernetes probes.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-31T17:30:00.000Z",
  "uptime_seconds": 3600.5
}
```

**Status Codes:**
- `200 OK`: Service is healthy

**Example Request:**
```bash
curl http://localhost:5001/health
```

## Configuration

The application can be configured using the following environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Host address to bind the server |
| `PORT` | `5001` | Port number to listen on |
| `DEBUG` | `False` | Enable debug mode (set to `true` to enable) |

## Project Structure

```
app_python/
├── app.py                    # Main application
├── requirements.txt          # Python dependencies
├── .gitignore               # Git ignore rules
├── README.md                # This file
├── tests/                   # Unit tests (for Lab 3)
│   └── __init__.py
└── docs/                    # Documentation
    ├── LAB01.md            # Lab submission documentation
    └── screenshots/        # Screenshots and proof of work
```

## Dependencies

- **Flask 3.1.0** - Lightweight web framework

See `requirements.txt` for pinned versions.

## Docker

The application is containerized and available on Docker Hub for easy deployment.

### Prerequisites

- **Docker:** 25+ or compatible version
- **Docker Hub account:** For pulling public images (optional for local builds)

### Building the Image Locally

Build the Docker image from source:

```bash
cd app_python

docker build -t <image-name>:<tag> .

# Example:
docker build -t devops-info-service:latest .
```

### Running a Container

Run the containerized application with port mapping:

```bash
docker run -d -p <host-port>:<container-port> --name <container-name> <image-name>:<tag>

# Example with default settings:
docker run -d -p 5001:5001 --name devops-app devops-info-service:latest

# Example with custom port and environment variables:
docker run -d -p 8080:5001 \
  -e PORT=5001 \
  -e DEBUG=false \
  --name devops-app \
  devops-info-service:latest
```

**Access the application:**
- Main endpoint: `http://localhost:5001/`
- Health check: `http://localhost:5001/health`

### Pulling from Docker Hub

Pull and run the pre-built image from Docker Hub:

```bash
docker pull <dockerhub-username>/<repository>:<tag>

# Example:
docker pull mirana18/devops-info-service:latest

# Run the pulled image
docker run -d -p 5001:5001 --name devops-app mirana18/devops-info-service:latest
```

### Container Management

```bash
# View running containers
docker ps

# View container logs
docker logs <container-name>
docker logs devops-app

# Stop a container
docker stop <container-name>

# Remove a container
docker rm <container-name>

# Stop and remove in one command
docker stop devops-app && docker rm devops-app
```

### Image Information

- **Base Image:** `python:3.13-slim`
- **Exposed Port:** `5001`
- **User:** Non-root user (`appuser`)
- **Health Check:** Built-in health check on `/health` endpoint
- **Image Size:** ~150MB (optimized with slim base and minimal dependencies)

### Docker Hub Repository

**Official Image:** [docker.io/mirana18/devops-info-service](https://hub.docker.com/r/mirana18/devops-info-service)

Available tags:
- `latest` - Most recent stable version
- `1.0.0` - Semantic versioning tags
- `lab02` - Lab-specific versions

## Development

### Unit Tests and Coverage

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest -v

# Run tests with coverage (70% threshold enforced in CI)
pytest --cov=. --cov-report=term-missing --cov-fail-under=70
```

**Coverage:** CI fails if coverage drops below 70%. Current coverage includes:
- All API endpoints (`GET /`, `GET /health`)
- JSON structure and required fields validation
- Error handling (404, 405)
- Helper functions (`format_uptime`, `get_system_info`)

### Testing

Test the endpoints using curl:

```bash
# Test main endpoint
curl http://localhost:5001/ | jq

# Test health endpoint
curl http://localhost:5001/health | jq
```

Or use a browser to visit:
- `http://localhost:5001/`
- `http://localhost:5001/health`

