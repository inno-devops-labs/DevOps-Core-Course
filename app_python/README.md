# DevOps Info Service

A FastAPI-based web service providing detailed information about the service, system, and runtime environment.

## Overview

This service is part of the DevOps course and provides:
- Comprehensive system information
- Health check endpoint for monitoring
- Runtime statistics
- Automatic OpenAPI documentation

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd app_python
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### Basic usage:
```bash
python app.py
```

### With custom configuration:
```bash
# Custom port
PORT=8080 python app.py

# Custom host and port
HOST=127.0.0.1 PORT=3000 python app.py

# Enable debug mode
DEBUG=true python app.py
```

### Using uvicorn directly:
```bash
uvicorn app:app --host 0.0.0.0 --port 5000 --reload
```

### Testing

Test the endpoints using curl:

```bash
# Get service info
curl http://localhost:5000/

# Health check
curl http://localhost:5000/health

# Pretty-print JSON output
curl http://localhost:5000/ | python -m json.tool
```

## API Endpoints

### GET `/`
Returns comprehensive service and system information.

**Example Response:**
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
    {"path": "/docs", "method": "GET", "description": "OpenAPI documentation"},
    {"path": "/redoc", "method": "GET", "description": "Alternative documentation"}
  ]
}
```

### GET `/health`
Health check endpoint for monitoring and Kubernetes probes.

**Example Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T14:30:00.000Z",
  "uptime_seconds": 3600
}
```

### GET `/docs`
Interactive OpenAPI/Swagger documentation.

### GET `/redoc`
Alternative API documentation interface.

## Configuration

The application can be configured using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Host to bind the server to |
| `PORT` | `5000` | Port to listen on |
| `DEBUG` | `False` | Enable debug mode and hot reload |