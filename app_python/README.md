# DevOps Info Service

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
git clone <repository-url>
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

## Project Structure

```
app_python/
├── app.py                  # Main application code
├── requirements.txt        # Python dependencies
├── .gitignore             # Git ignore patterns
├── README.md              # This file
├── tests/                 # Unit tests (Lab 3)
│   └── __init__.py
└── docs/                  # Lab documentation
    ├── LAB01.md          # Lab submission document
    └── screenshots/      # Proof of work
```

## Dependencies

- **Flask 3.1.0:** Web framework for building the API
- **Werkzeug 3.1.3:** WSGI utility library for Flask
- **requests 2.32.3:** HTTP library for making requests

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

## Troubleshooting

### Port Already in Use

If you see "Address already in use" error:

```bash
# Use a different port
PORT=8080 python app.py
```

### Module Not Found

If you see "ModuleNotFoundError":

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```
