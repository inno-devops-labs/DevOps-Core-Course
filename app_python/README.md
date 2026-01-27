# DevOps Info Service

A lightweight web service that provides comprehensive system and runtime information for DevOps monitoring and diagnostics.

## Overview

DevOps Info Service is a Python-based web application that exposes system information, runtime metrics, and health status through a simple REST API. Built with Flask, it serves as a foundation for learning DevOps practices including containerization, CI/CD, and monitoring.

## Prerequisites

- **Python**: 3.11 or higher
- **pip**: Latest version recommended
- **Virtual environment**: venv or virtualenv

## Installation

1. **Clone the repository** (if not already done)

2. **Create and activate virtual environment:**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

## Running the Application

**Default configuration** (listens on 0.0.0.0:8080):

```bash
python app.py
```

**Custom port:**

```bash
PORT=3000 python app.py
```

**Custom host and port:**

```bash
HOST=127.0.0.1 PORT=8080 python app.py
```

**Enable debug mode:**

```bash
DEBUG=true python app.py
```

## API Endpoints

### `GET /`

Returns comprehensive service and system information including:
- Service metadata (name, version, framework)
- System information (hostname, platform, CPU count)
- Runtime metrics (uptime, current time)
- Request details (client IP, user agent)
- Available endpoints

**Example request:**

```bash
curl http://localhost:8080/
```

**Example response:**

```json
{
  "endpoints": [
    {
      "description": "Service information",
      "method": "GET",
      "path": "/"
    },
    {
      "description": "Health check",
      "method": "GET",
      "path": "/health"
    }
  ],
  "request": {
    "client_ip": "127.0.0.1",
    "method": "GET",
    "path": "/",
    "user_agent": "curl/8.7.1"
  },
  "runtime": {
    "current_time": "2026-01-27T10:12:24.616261+00:00",
    "timezone": "UTC",
    "uptime_human": "1 hour, 2 minutes",
    "uptime_seconds": 3765
  },
  "service": {
    "description": "DevOps course info service",
    "framework": "Flask",
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "system": {
    "architecture": "arm64",
    "cpu_count": 11,
    "hostname": "MacBook-Pro--Egor.local",
    "platform": "Darwin",
    "platform_version": "Darwin Kernel Version 25.2.0: Tue Nov 18 21:09:45 PST 2025; root:xnu-12377.61.12~1/RELEASE_ARM64_T6030",
    "python_version": "3.12.3"
  }
}
```

### `GET /health`

Simple health check endpoint for monitoring systems and Kubernetes probes.

**Example request:**

```bash
curl http://localhost:8080/health
```

**Example response:**

```json
{
  "status": "healthy",
  "timestamp": "2026-01-27T10:15:11.908501+00:00",
  "uptime_seconds": 3932
}
```

**Status:** Always returns HTTP 200 when service is running.

## Configuration

The application supports the following environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8080` | Server port |
| `DEBUG` | `False` | Enable Flask debug mode |

## Project Structure

```
app_python/
├── app.py              # Main application
├── requirements.txt    # Python dependencies
├── .gitignore         # Git ignore rules
├── README.md          # This file
├── tests/             # Unit tests
│   └── __init__.py
└── docs/              # Lab documentation
    ├── LAB01.md
    └── screenshots/
```

## Development

The application follows Python best practices:
- PEP 8 code style
- Clean code organization
- Proper error handling
- Structured logging
- Environment-based configuration

## Testing

Access the endpoints using curl, HTTPie, or Postman:

```bash
# Test main endpoint
curl http://localhost:8080/

# Test health check
curl http://localhost:8080/health

# Pretty print with jq
curl -s http://localhost:8080/ | jq

# Using HTTPie
http localhost:8080/
```
