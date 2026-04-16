# DevOps Info Service

[![Python CI (app_python)](https://github.com/MariaRokkel/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg?branch=lab03)](https://github.com/MariaRokkel/DevOps-Core-Course/actions/workflows/python-ci.yml)

## Overview
DevOps Info Service is a Python web application that provides detailed information about the service itself, the host system, runtime, and HTTP requests. It also includes a health check endpoint for monitoring and Kubernetes probes. The service is lightweight, configurable via environment variables, and suitable for DevOps experiments and labs.

## Prerequisites
- Python 3.11+
- pip
- Virtual environment (recommended)
- macOS or Linux

## Installation

1. Clone your fork and navigate to the project folder:

```bash
git clone <your-fork-url>
cd <course-repo>/app_python
```

2. Create and activate a virtual environment:

**macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (PowerShell):**

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Testing

We use **pytest** because it is lightweight, has a clean test syntax, and works well with Flask's built-in test client.

Install dev dependencies:

```bash
pip install -r requirements-dev.txt
```

Run tests:

```bash
pytest
```

## Running the Application

**Default run:**

```bash
python app.py
```

**Custom configuration via environment variables:**

```bash
HOST=127.0.0.1 PORT=8080 DEBUG=True python app.py
```

> ⚠️ On macOS, port 5000 may already be used by system services (e.g., AirPlay Receiver). Use a different PORT if needed.

The service will start and listen on the configured host and port.

## Docker

The application can be containerized using Docker for consistent deployment across environments.

### Building the Image

Build the Docker image locally:

```bash
docker build -t <your-dockerhub-username>/devops-info-service:<tag> .
```

Replace `<your-dockerhub-username>` with your Docker Hub username and `<tag>` with a version tag (e.g., `latest`, `v1.0.0`).

### Running the Container

Run a container from the built image with port mapping:

```bash
docker run -p <host-port>:5000 <your-dockerhub-username>/devops-info-service:<tag>
```

Replace `<host-port>` with the port you want to use on your host machine (e.g., `8080`).

**Example:**
```bash
docker run -p 8080:5000 <your-dockerhub-username>/devops-info-service:latest
```

The service will be accessible at `http://localhost:8080`.

### Custom Configuration

You can override environment variables when running the container:

```bash
docker run -p 8080:5000 -e PORT=5000 -e DEBUG=false <your-dockerhub-username>/devops-info-service:<tag>
```

### Pulling from Docker Hub

If the image is published to Docker Hub, you can pull and run it:

```bash
docker pull <your-dockerhub-username>/devops-info-service:<tag>
docker run -p 8080:5000 <your-dockerhub-username>/devops-info-service:<tag>
```

For detailed Docker implementation documentation, see [docs/LAB02.md](docs/LAB02.md).

## API Endpoints

### GET /

Returns information about the service, system, runtime, and request.

**Response Example:**

```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Flask"
  },
  "system": {
    "hostname": "my-macbook",
    "platform": "Darwin",
    "platform_version": "21.6.0",
    "architecture": "x86_64",
    "cpu_count": 8,
    "python_version": "3.13.1"
  },
  "runtime": {
    "uptime_seconds": 3600,
    "uptime_human": "1 hours, 0 minutes",
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
    "count": 3,
    "file": "/data/visits"
  },
  "endpoints": [
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/health", "method": "GET", "description": "Health check"},
    {"path": "/visits", "method": "GET", "description": "Visits counter"}
  ]
}
```

Each `GET /` increments a persisted visit counter stored at `VISITS_FILE` (default `/data/visits`).

### GET /health

Returns service health status.

**Response Example:**

```json
{
  "status": "healthy",
  "timestamp": "2026-01-07T14:30:00.000Z",
  "uptime_seconds": 3600
}
```

### GET /visits

Returns the current visit count (read from `VISITS_FILE` without incrementing).

**Response Example:**

```json
{
  "visits": 12,
  "file": "/data/visits"
}
```

## Configuration

Environment variables for customization:

| Variable | Default | Description |
|----------|---------|-------------|
| HOST | 0.0.0.0 | IP address to bind the service |
| PORT | 5000 | Port to run the service |
| DEBUG | False | Flask debug mode |
| VISITS_FILE | /data/visits | Path to the persisted visits counter file |

**Example:**

```bash
HOST=127.0.0.1 PORT=8080 DEBUG=True python app.py
```

## Docker Compose (persistent visits)

From `app_python/`:

```bash
docker compose up --build -d
curl -s http://localhost:8080/visits
curl -s http://localhost:8080/
cat ./data/visits
docker compose restart
curl -s http://localhost:8080/visits
```

`docker-compose.yml` binds `./data` on the host to `/app/data` in the container and sets `VISITS_FILE=/app/data/visits`.

## Logging

Logs all requests to console.

**Format:** `timestamp - logger_name - level - message`

**Example:**

```
2026-01-07 14:30:00 - __main__ - INFO - GET /
```

## Error Handling

### 404 Not Found

```json
{
  "error": "Not Found",
  "message": "Endpoint does not exist"
}
```

### 500 Internal Server Error

```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred"
}
```

## Screenshots

For lab documentation, save screenshots in:

```
docs/screenshots/01-main-endpoint.png
docs/screenshots/02-health-check.png
docs/screenshots/03-formatted-output.png
```
