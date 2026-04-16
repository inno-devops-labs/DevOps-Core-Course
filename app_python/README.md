# DevOps Info Service

[![Python CI](https://github.com/4hellboy4/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)](https://github.com/4hellboy4/DevOps-Core-Course/actions/workflows/python-ci.yml)
[![codecov](https://codecov.io/gh/4hellboy4/DevOps-Core-Course/branch/master/graph/badge.svg)](https://codecov.io/gh/4hellboy4/DevOps-Core-Course)

A web service that reports system information and health status, built with FastAPI.

## Overview

DevOps Info Service provides detailed information about itself and its runtime environment through a REST API. It exposes system metadata, uptime tracking, and a health check endpoint for monitoring.

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

```bash
python app.py
```

With custom configuration:

```bash
PORT=8080 python app.py
HOST=127.0.0.1 PORT=3000 python app.py
```

Or directly via uvicorn (with auto-reload for development):

```bash
uvicorn app:app --reload --port 8000
```

## API Endpoints

| Method | Path      | Description                          |
|--------|-----------|--------------------------------------|
| GET    | `/`       | Service and system information (increments visit counter) |
| GET    | `/visits` | Current persisted visit count          |
| GET    | `/health` | Health check (status, uptime)        |

### `GET /`

Returns comprehensive service, system, runtime, and request information.

```bash
curl http://localhost:8000/
```

Example response:

```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "my-laptop",
    "platform": "Darwin",
    "platform_version": "macOS-15.2-arm64-arm-64bit",
    "architecture": "arm64",
    "cpu_count": 8,
    "python_version": "3.13.1"
  },
  "runtime": {
    "uptime_seconds": 120,
    "uptime_human": "0 hours, 2 minutes",
    "current_time": "2026-02-11T14:30:00.000000+00:00",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/8.7.1",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/health", "method": "GET", "description": "Health check"}
  ]
}
```

### `GET /health`

Returns service health status and uptime.

```bash
curl http://localhost:8000/health
```

Example response:

```json
{
  "status": "healthy",
  "timestamp": "2026-02-11T14:30:00.000000+00:00",
  "uptime_seconds": 120
}
```

## Testing

Install dev dependencies:

```bash
pip install -r requirements-dev.txt
```

Run tests:

```bash
pytest -v
```

Run with coverage:

```bash
pytest --cov=. --cov-report=term
```

## Configuration

| Variable           | Default        | Description                              |
|--------------------|----------------|------------------------------------------|
| `HOST`             | `0.0.0.0`      | Server bind address                      |
| `PORT`             | `8000`         | Server port                              |
| `DEBUG`            | `false`        | Enable debug mode                        |
| `VISITS_FILE_PATH` | `/data/visits` | File where the visit counter is stored   |

Visit counter: each `GET /` increments an integer persisted in `VISITS_FILE_PATH` (directory is created if needed). Use a mounted volume in Docker/Kubernetes so the count survives restarts.

## Docker Compose (local persistence)

From `app_python/`:

```bash
docker compose up --build
```

The compose file mounts `./data` on the host to `/data` in the container so `./data/visits` keeps the counter across container restarts.

## Docker

### Build the image

```bash
docker build -t devops-info-service .
```

### Run a container

```bash
docker run -p 8000:8000 devops-info-service
```

With custom port:

```bash
docker run -p 3000:8000 devops-info-service
```

### Pull from Docker Hub

```bash
docker pull 4hellboy4/devops-info-service:latest
docker run -p 8000:8000 4hellboy4/devops-info-service:latest
```

## Project Structure

```
app_python/
├── app.py                # Application entry point
├── config.py             # Environment variable configuration
├── requirements.txt      # Pinned dependencies
├── .gitignore
├── README.md
├── models/               # Pydantic response schemas
│   ├── root_responses.py
│   └── health_responses.py
├── routes/               # Endpoint handlers
│   ├── root.py
│   └── health.py
├── services/             # Business logic
│   ├── system_info.py
│   ├── uptime.py
│   └── visits_counter.py
├── docker-compose.yml    # Local run with ./data volume
├── tests/
└── docs/
    └── LAB01.md
```
