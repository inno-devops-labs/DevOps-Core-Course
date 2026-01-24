# DevOps Info Service

## Overview

A lightweight FastAPI-based service that provides comprehensive system and runtime information. This service exposes REST API endpoints to retrieve service metadata, system information, and health status. Ideal for monitoring, debugging, and DevOps observability in containerized environments.

**Key Features:**
- Real-time system information (CPU, platform, architecture)
- Service uptime tracking and human-readable formatting
- Request metadata capture (client IP, user agent, path)
- Health check endpoint for load balancers and orchestrators
- Environment-based configuration
- FastAPI with automatic OpenAPI documentation

---

## Prerequisites

- **Python:** 3.8 or higher
- **pip:** Package manager (comes with Python)
- **Virtual Environment:** Recommended for isolation

**Core Dependencies:**
- `fastapi` - Modern web framework
- `uvicorn` - ASGI server

---

## Installation

### 1. Create and Activate Virtual Environment

```bash
python -m venv venv
source venv/bin/activate
```

> On Windows, use: `venv\Scripts\activate`

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Running the Application

### Basic Usage

```bash
python app.py
```

The service starts on `http://localhost:5000` by default.

### With Custom Configuration

```bash
# Custom port
PORT=8080 python app.py

# Custom host and port
HOST=127.0.0.1 PORT=8080 python app.py

# Enable debug mode with auto-reload
DEBUG=true PORT=3000 python app.py
```

### Using Uvicorn Directly

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

---

## API Endpoints

### GET `/`

**Description:** Returns comprehensive service and system information

**Response Example:**
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "mycomputer",
    "platform": "Darwin",
    "platform_version": "23.1.0",
    "architecture": "arm64",
    "cpu_count": 8,
    "python_version": "3.11.0"
  },
  "runtime": {
    "uptime_seconds": 3600,
    "uptime_human": "1 hour, 0 minutes",
    "current_time": "2024-01-15T14:30:00.000000+00:00",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/7.64.1",
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

### GET `/health`

**Description:** Minimal health check endpoint for load balancers and monitoring systems

**Response Example:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T14:30:00.000000+00:00",
  "uptime_seconds": 3600
}
```

**Use Cases:**
- Kubernetes liveness probes
- Load balancer health checks
- Monitoring and alerting systems

---

## Configuration

All configuration is done via environment variables. Set them before running the application:

| Variable | Default | Type | Description |
|----------|---------|------|-------------|
| `HOST` | `0.0.0.0` | String | Bind address for the service |
| `PORT` | `5000` | Integer | Service port |
| `DEBUG` | `False` | Boolean | Enable debug mode with auto-reload (accepts `"true"` or `"false"`) |

### Example Configuration

```bash
# Production setup
HOST=0.0.0.0 PORT=8000 DEBUG=false python app.py

# Development setup
HOST=localhost PORT=3000 DEBUG=true python app.py

# Docker/Kubernetes setup
HOST=0.0.0.0 PORT=8080 python app.py
```

