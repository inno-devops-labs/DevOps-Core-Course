# DevOps Info Service

[![Python CI](https://github.com/almax07082005/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)](https://github.com/almax07082005/DevOps-Core-Course/actions/workflows/python-ci.yml)

A production-ready Python web service that provides comprehensive system and runtime information.

## Overview

The DevOps Info Service is a lightweight web application built to report detailed information about itself and its runtime environment. It exposes two main endpoints for service information and health checking, making it ideal for monitoring and DevOps workflows.

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- Virtual environment (recommended)

## Installation

1. Clone the repository and navigate to the app directory:
```bash
cd app_python
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

### Default Configuration

```bash
python app.py
```

The service will start on `0.0.0.0:5000` by default.

### Custom Configuration

Use environment variables to customize the service:

```bash
PORT=8080 python app.py
```

```bash
HOST=127.0.0.1 PORT=3000 DEBUG=true python app.py
```

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
    "platform_version": "macOS-13.4-x86_64",
    "architecture": "x86_64",
    "cpu_count": 8,
    "python_version": "3.11.5"
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
    {"path": "/health", "method": "GET", "description": "Health check"}
  ]
}
```

### `GET /health`

Health check endpoint for monitoring and orchestration.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-07T14:30:00.000Z",
  "uptime_seconds": 3600
}
```

## Configuration

The service can be configured using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Host address to bind to |
| `PORT` | `5000` | Port number to listen on |
| `DEBUG` | `False` | Enable debug mode |

## Docker

The application is containerized and available on Docker Hub.

### Building the Image

```bash
docker build -t <your-username>/devops-info-service:latest .
```

### Running with Docker

```bash
docker run -d -p 5000:5000 --name devops-service <your-username>/devops-info-service:latest
```

### Pulling from Docker Hub

```bash
docker pull <your-username>/devops-info-service:latest
docker run -d -p 5000:5000 --name devops-service <your-username>/devops-info-service:latest
```

### Testing the Container

```bash
curl http://localhost:5000/
curl http://localhost:5000/health
```

## Testing

### Unit Tests

Install dev dependencies and run tests:

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest tests/ -v
```

With venv: `source venv/bin/activate && pytest tests/ -v`

### Manual Testing

```bash
curl http://localhost:5000/
curl http://localhost:5000/health
curl http://localhost:5000/ | jq .
```

## Architecture

The service is built with:
- **Flask 3.1**: Lightweight WSGI web framework
- **Python Standard Library**: Platform, socket, datetime modules for system introspection
- **Logging**: Structured logging for production monitoring
- **Error Handling**: Custom error handlers for 404 and 500 responses

## Development

The project follows Python best practices:
- PEP 8 compliant code style
- Type hints for better IDE support
- Modular function design
- Comprehensive error handling
- Production-ready logging
