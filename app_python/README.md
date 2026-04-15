# DevOps Info Service

## Overview

The DevOps Info Service is a RESTful web application built with Flask that exposes system information, runtime metrics, health status, and a persistent visits counter. It's designed to be lightweight, configurable, and production-ready, with proper error handling, logging, and documentation.

## CI/CD Status



[![Python CI](https://github.com/Rash1d1/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg?branch=master)](https://github.com/Rash1d1/DevOps-Core-Course/actions/workflows/python-ci.yml)
[![Coverage](https://codecov.io/gh/Rash1d1/DevOps-Core-Course/branch/master/graph/badge.svg)](https://codecov.io/gh/Rash1d1/DevOps-Core-Course)

## Prerequisites

- **Python 3.11+**
- **pip** (Python package installer)
- **virtualenv** (recommended for isolated environments)

## Installation

1. **Clone the repository** (if applicable):
   ```bash
   git clone <repository-url>
   cd app_python
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install development tools (optional)**:

   If you are working on the code locally, you can install testing and linting tools:

   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### Basic Usage

Run the application with default settings (listens on `0.0.0.0:5000`):

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

### Verify Installation

Once the application is running, test the endpoints:

```bash
# Main endpoint
curl http://localhost:5000/

# Health check
curl http://localhost:5000/health

# Persistent visits counter
curl http://localhost:5000/visits

# Pretty-printed JSON (requires jq)
curl http://localhost:5000/ | jq
```

## Running Tests

This project uses **pytest** for unit tests and **pytest-cov** for coverage.

From the `app_python/` directory:

```bash
pytest
```

Run tests with coverage (the same way CI does):

```bash
pytest --cov=. --cov-report=term --cov-report=xml
```

The XML report `coverage.xml` is consumed by Codecov in the CI pipeline.

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
    "platform": "Linux",
    "platform_version": "Linux-6.8.0-58-generic-x86_64-with-glibc2.39",
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
  "visits": {
    "count": 42,
    "file": "/data/visits"
  },
  "endpoints": [
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/health", "method": "GET", "description": "Health check"},
    {"path": "/metrics", "method": "GET", "description": "Prometheus metrics endpoint"},
    {"path": "/visits", "method": "GET", "description": "Current visits counter value"}
  ]
}
```

### `GET /health`

Returns health status for monitoring and Kubernetes probes.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T14:30:00.000Z",
  "uptime_seconds": 3600
}
```

**Status Codes:**
- `200 OK` - Service is healthy

### `GET /visits`

Returns the current persistent visits counter without incrementing it.

**Response:**
```json
{
  "visits": 42
}
```

## Configuration

The application can be configured using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Host address to bind to |
| `PORT` | `5000` | Port number to listen on |
| `DEBUG` | `False` | Enable debug mode (set to `true` to enable) |
| `VISITS_FILE` | `data/visits` | File path used to persist the visits counter |

### Examples

```bash
# Development (localhost only)
HOST=127.0.0.1 PORT=3000 python app.py

# Production (all interfaces)
HOST=0.0.0.0 PORT=8080 python app.py

# Debug mode
DEBUG=true python app.py

# Custom persistent counter file
VISITS_FILE=./data/visits python app.py
```

## Project Structure

```
app_python/
├── app.py                    # Main application
├── requirements.txt          # Dependencies
├── .gitignore               # Git ignore rules
├── README.md                # This file
├── tests/                   # Unit tests (Lab 3)
│   └── __init__.py
└── docs/                    # Lab documentation
    ├── LAB01.md            # Lab submission
    └── screenshots/        # Proof of work
```

## Development

### Code Style

This project follows PEP 8 style guidelines. Key practices:
- 4 spaces for indentation
- Maximum line length of 79 characters (soft limit 99)
- Clear function and variable names
- Docstrings for functions
- Proper import organization

### Logging

The application uses Python's `logging` module with INFO level by default. Logs include:
- Application startup
- Request information (method, path, client IP)
- Error details

### Error Handling

The application includes error handlers for:
- `404 Not Found` - Invalid endpoints
- `500 Internal Server Error` - Unexpected errors

All errors return JSON responses for consistency.

## Docker

You can run this application inside a Docker container instead of managing Python and dependencies directly on your host.

### Build Image

Run from the `app_python/` directory:

```bash
docker build -t <your-dockerhub-username>/devops-info-service:<your-tag> .
```

- **`-t`**: Names/tags the image (include your Docker Hub username)
- **`.`**: Uses the current directory as the build context

### Run Container


```bash
docker run \
  -p 5000:5000 \
  -e HOST=0.0.0.0 \
  -e PORT=5000 \
  <your-dockerhub-username>/devops-info-service:<your_tag>
```

- **`-p 5000:5000`**: Maps host port 5000 to container port 5000
- **`-e`**: Overrides environment variables if needed

You should then be able to access:

- Main endpoint: `http://localhost:5000/`
- Health check: `http://localhost:5000/health`

### Pull from Docker Hub

After pushing your image to Docker Hub, you (or anyone else) can pull and run it:

```bash
docker pull <your-dockerhub-username>/devops-info-service:<your_tag>

docker run -p 5000:5000 <your-dockerhub-username>/devops-info-service:<your_tag>
```

### Local Persistence Test with Docker Compose

From `app_python/`:

```bash
docker compose up --build -d
curl -s http://localhost:5000/ >/dev/null
curl -s http://localhost:5000/ >/dev/null
curl http://localhost:5000/visits
cat ./data/visits

docker compose restart
curl http://localhost:5000/visits
```

Compose mounts `./data` from host to `/app/data` in the container and sets
`VISITS_FILE=/app/data/visits`, so the counter survives container restarts.
