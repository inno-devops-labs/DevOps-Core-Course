# DevOps Info Service

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
  "endpoints": [
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/health", "method": "GET", "description": "Health check"}
  ]
}
```

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

## Configuration

Environment variables for customization:

| Variable | Default | Description |
|----------|---------|-------------|
| HOST | 0.0.0.0 | IP address to bind the service |
| PORT | 5000 | Port to run the service |
| DEBUG | False | Flask debug mode |

**Example:**

```bash
HOST=127.0.0.1 PORT=8080 DEBUG=True python app.py
```

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
