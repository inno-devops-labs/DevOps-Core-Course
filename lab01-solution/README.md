# DevOps Info Service

A production-ready Python web service built with FastAPI that provides comprehensive information about itself and its runtime environment.

## Overview

The DevOps Info Service is a lightweight, fast web application designed to report detailed system and application information. It serves as the foundation for a comprehensive monitoring and DevOps tooling system that will evolve throughout a DevOps course.

## Prerequisites

- **Python:** 3.11 or higher
- **pip:** Package installer for Python
- **virtualenv** (optional): For creating isolated environments

## Installation

1. **Clone and navigate to the project:**
   ```bash
   cd lab01-solution
   ```

2. **Create a virtual environment:**
   ```bash
   # On Windows
   python -m venv venv
   venv\Scripts\activate
   
   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### Default Mode (0.0.0.0:8000)
```bash
python app.py
```

### Custom Port
```bash
PORT=5000 python app.py
```

### Custom Host and Port
```bash
HOST=127.0.0.1 PORT=3000 python app.py
```

### Debug Mode (auto-reload on file changes)
```bash
DEBUG=true PORT=8000 python app.py
```

### Using Uvicorn Directly
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Once running, the application will be available at:
- **Application:** `http://localhost:8000` (Main endpoint)
- **API Documentation:** `http://localhost:8000/docs` (Interactive Swagger UI)
- **Health check:** `http://localhost:8000/health` (Check if the application is avialable?)

## API Endpoints

### 1. GET / — Service Information

Returns comprehensive service and system information.

**Request:**
```bash
curl -X GET http://localhost:8000/
```

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
    "hostname": "DESKTOP-ABC123",
    "platform": "Windows",
    "platform_version": "Windows 10",
    "architecture": "AMD64",
    "cpu_count": 8,
    "python_version": "3.13.1"
  },
  "runtime": {
    "uptime_seconds": 3600,
    "uptime_human": "1 hour, 0 minutes",
    "current_time": "2026-01-28T14:30:00Z",
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
      "description": "Service and system information"
    },
    {
      "path": "/health",
      "method": "GET",
      "description": "Health check endpoint"
    }
  ]
}
```

### 2. GET /health — Health Check

Simple health check endpoint for monitoring and Kubernetes liveness/readiness probes.

**Request:**
```bash
curl -X GET http://localhost:8000/health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T14:30:00Z",
  "uptime_seconds": 3600
}
```

## Configuration

Configure the application behavior using environment variables:

| Variable | Default | Description | Example |
|----------|---------|-------------|---------|
| `HOST` | `0.0.0.0` | Server bind address | `127.0.0.1` |
| `PORT` | `8000` | Server port | `5000` |
| `DEBUG` | `False` | Enable debug mode and auto-reload | `true` |

**Examples:**
```bash
# Production-like setup (localhost only)
HOST=127.0.0.1 PORT=8000 python app.py

# Accessible from network
HOST=0.0.0.0 PORT=5000 python app.py

# Development with auto-reload
DEBUG=true PORT=8080 python app.py
```

## Testing the API

### Using curl
```bash
# Main endpoint
curl http://localhost:8000/

# With pretty JSON output (requires jq)
curl http://localhost:8000/ | jq .

# Health check
curl http://localhost:8000/health

# With verbose output
curl -v http://localhost:8000/

# Custom host/port
curl http://127.0.0.1:5000/
```

### Using HTTPie (more user-friendly)
```bash
http GET localhost:8000/
http GET localhost:8000/health
```

### Using Python requests
```python
import requests

response = requests.get('http://localhost:8000/')
print(response.json())

health = requests.get('http://localhost:8000/health')
print(health.json())
```

### Using the Built-in Swagger UI
Navigate to `http://localhost:8000/docs` in your browser to interactively test the API.

## Project Structure

```
lab01-solution/
├── app.py                    # Main application with FastAPI setup
├── requirements.txt          # Python dependencies with pinned versions
├── .gitignore               # Git ignore patterns
├── README.md                # This file - user-facing documentation
├── tests/                   # Test directory (for future labs)
│   └── __init__.py
└── docs/                    # Documentation
    ├── LAB01.md            # Lab submission and implementation details
    └── screenshots/        # Evidence of functionality
```

## Development

### Logging
The application includes structured logging:
- Startup and shutdown events
- Request handling information
- Error tracking and reporting

All logs are formatted with timestamp, logger name, level, and message:
```
2026-01-28 14:30:00,123 - __main__ - INFO - DevOps Info Service starting on 0.0.0.0:8000
```

### Error Handling
- **404 Not Found:** Returns JSON error response for non-existent endpoints
- **500 Internal Server Error:** Gracefully handles unexpected errors with JSON response

## Dependencies

- **FastAPI** (0.115.0) - Modern, fast web framework with automatic API documentation
- **Uvicorn** (0.32.0) - ASGI web server with streaming support
- **python-multipart** (0.0.6) - Streaming upload support for FastAPI

All dependencies are pinned to specific versions for reproducibility and stability.

## Troubleshooting

### Port Already in Use
If you see "Address already in use" error:
```bash
# Use a different port
PORT=8001 python app.py
```

## Framework Choice: FastAPI

See [docs/LAB01.md](docs/LAB01.md) for detailed info.
