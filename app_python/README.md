# DevOps Info Service - Python

A production-ready web service providing comprehensive system information and health checks. Built with FastAPI for high performance and automatic API documentation.

## Overview

- **Service Information**: Application metadata and framework details
- **System Introspection**: Real-time OS, CPU, and Python version information
- **Runtime Monitoring**: Uptime tracking and timestamped responses
- **Health Checks**: Kubernetes-compatible liveness/readiness probe endpoint
- **Request Tracking**: Client IP, user agent, and request path logging
- **Environment Configuration**: PORT and HOST customization via env vars

## Prerequisites

- **Python 3.11+**
- **pip** package manager
- Virtual environment (recommended)

## Installation

1. Clone the repository and navigate to the project:
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

### Default Configuration (0.0.0.0:5000)
```bash
python app.py
```

### Custom Port
```bash
PORT=8080 python app.py
```

### Custom Host and Port
```bash
HOST=127.0.0.1 PORT=3000 python app.py
```

### Debug Mode
```bash
DEBUG=true python app.py
```

The application will output:
```
INFO:devops-info-service: Starting DevOps Info Service (FastAPI)
INFO:uvicorn.server:Uvicorn running on http://0.0.0.0:5000
```

## API Endpoints

### GET /

Returns comprehensive service and system information.

**Response (200 OK):**
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "LAPTOP-LJVRUS9G",
    "platform": "Linux",
    "platform_version": "#1 SMP Fri Mar 29 23:14:13 UTC 2024",
    "architecture": "x86_64",
    "cpu_count": 20,
    "python_version": "3.10.12"
  },
  "runtime": {
    "uptime_seconds": 6,
    "uptime_human": "0 hours, 0 minutes",
    "current_time": "2026-01-24T17:07:43.217902Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/7.81.0",
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

Simple health check endpoint.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-24T17:07:54.041701Z",
  "uptime_seconds": 17
}
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| HOST | 0.0.0.0 | Server bind address |
| PORT | 5000 | Server port |
| DEBUG | false | Enable debug mode and verbose logging |
