# DevOps Info Service

A production-ready web service providing detailed information about itself and its runtime environment. This service is built as part of the DevOps Core Course and will evolve throughout the course with containerization, CI/CD, monitoring, and persistence features.

## Overview

The DevOps Info Service exposes REST API endpoints that return:
- Service metadata (name, version, framework)
- System information (hostname, platform, CPU, Python version)
- Runtime metrics (uptime, current time)
- Request details (client IP, user agent)
- Health status for monitoring

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

## Installation

1. **Clone the repository** (if not already done):
   ```bash
   cd app_python
   ```

2. **Create a virtual environment**:
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

### Default Configuration
```bash
python app.py
# Server runs on http://0.0.0.0:5000
```

### Custom Port
```bash
PORT=8080 python app.py
# Server runs on http://0.0.0.0:8080
```

### Custom Host and Port
```bash
HOST=127.0.0.1 PORT=3000 python app.py
# Server runs on http://127.0.0.1:3000
```

### Debug Mode
```bash
DEBUG=true python app.py
```

## API Endpoints

### `GET /` - Service Information

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
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "my-laptop",
    "platform": "Linux",
    "platform_version": "Linux-5.15.0-x86_64",
    "architecture": "x86_64",
    "cpu_count": 8,
    "python_version": "3.11.0"
  },
  "runtime": {
    "uptime_seconds": 3600,
    "uptime_human": "1 hour, 0 minutes",
    "current_time": "2026-01-26T16:30:00.000Z",
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

### `GET /health` - Health Check

Simple health endpoint for monitoring and Kubernetes probes.

**Request:**
```bash
curl http://localhost:5000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-26T16:30:00.000Z",
  "uptime_seconds": 3600
}
```

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `HOST` | `0.0.0.0` | Host address to bind |
| `PORT` | `5000` | Port number to listen on |
| `DEBUG` | `False` | Enable debug mode |

## Project Structure

```
app_python/
├── app.py                # Main application
├── requirements.txt      # Dependencies
├── .gitignore           # Git ignore rules
├── README.md            # This file
├── tests/               # Unit tests (Lab 3)
│   └── __init__.py
└── docs/                # Documentation
    ├── LAB01.md        # Lab submission document
    └── screenshots/    # Proof of work screenshots
```

## API Documentation

FastAPI provides automatic interactive API documentation:
- **Swagger UI**: http://localhost:5000/docs
- **ReDoc**: http://localhost:5000/redoc

## Future Enhancements

This service will be extended in future labs:
- Lab 2: Docker containerization
- Lab 3: Unit tests and CI/CD
- Lab 8: Prometheus metrics endpoint
- Lab 9: Kubernetes deployment
- Lab 12: File persistence
- Lab 13: Multi-environment GitOps
