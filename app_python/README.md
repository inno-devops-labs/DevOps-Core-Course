# DevOps Info Service

A modern Python web service built with FastAPI that provides detailed information about itself and its runtime environment. Features auto-generated interactive API documentation and comprehensive system introspection capabilities.

## Overview

This service exposes RESTful endpoints that return JSON-formatted information about:
- Service metadata (name, version, framework)
- System information (hostname, platform, architecture, CPU count)
- Runtime metrics (uptime, current time)
- Request details (client IP, user agent, HTTP method)
- Health status for monitoring

**Key Feature:** FastAPI automatically generates interactive API documentation at `/docs` (Swagger UI) and `/redoc` (ReDoc).

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Virtual environment (recommended)

## Installation

1. **Clone the repository** (or navigate to the project directory)

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   - On Linux/Mac:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### Basic Usage

Run with default configuration (0.0.0.0:8000):
```bash
python app.py
```

### Using Uvicorn Directly

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
# With auto-reload for development
uvicorn app:app --reload
```

### Custom Configuration

Use environment variables to customize the service:

```bash
# Custom port
PORT=8080 python app.py

# Custom host and port
HOST=127.0.0.1 PORT=3000 python app.py

# Enable debug mode
DEBUG=true python app.py
```

## API Documentation

### Auto-Generated Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI:** http://localhost:8000/docs
  - Interactive interface to test endpoints
  - Request/response examples
  - Try out API calls directly in the browser

- **ReDoc:** http://localhost:8000/redoc
  - Alternative documentation view
  - Clean, responsive design
  - Detailed schema information

### Manual Endpoints

#### GET /

Returns comprehensive service and system information.

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
    "hostname": "my-laptop",
    "platform": "Linux",
    "platform_version": "5.15.0",
    "architecture": "x86_64",
    "cpu_count": 8,
    "python_version": "3.11.0"
  },
  "runtime": {
    "uptime_seconds": 3600,
    "uptime_human": "1 hours, 0 minutes",
    "current_time": "2026-01-27T11:53:00.000Z",
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
    {"path": "/docs", "method": "GET", "description": "Interactive API documentation (Swagger UI)"},
    {"path": "/redoc", "method": "GET", "description": "Alternative API documentation (ReDoc)"}
  ]
}
```

**Testing:**
```bash
curl http://localhost:8000/
# Or with formatted output
curl http://localhost:8000/ | python -m json.tool
```

#### GET /health

Simple health check endpoint for monitoring and orchestration systems.

**Response Example:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-27T11:53:00.000Z",
  "uptime_seconds": 3600
}
```

**Testing:**
```bash
curl http://localhost:8000/health
```

## Configuration

The service can be configured using the following environment variables:

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `HOST` | Host address to bind to | `0.0.0.0` | `127.0.0.1` |
| `PORT` | Port number to listen on | `8000` | `8080` |
| `DEBUG` | Enable debug logging | `False` | `true` |

## Project Structure

```
app_python/
├── app.py                 # Main FastAPI application
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore rules
├── README.md             # This file
├── tests/                # Unit tests (for Lab 3)
│   └── __init__.py
└── docs/                 # Lab documentation
    ├── LAB01.md         # Lab submission document
    └── screenshots/     # Testing evidence
```

## Why FastAPI?

FastAPI offers several advantages over traditional frameworks:

1. **Automatic Documentation:** OpenAPI/Swagger UI and ReDoc generated automatically
2. **Type Safety:** Python type hints enable better IDE support and validation
3. **Performance:** Built on Starlette and Pydantic, FastAPI is one of the fastest Python frameworks
4. **Modern:** Native async/await support for high-performance async endpoints
5. **Developer Experience:** Automatic request validation, serialization, and error handling

## Development

### Code Quality

This project follows:
- PEP 8 style guidelines
- Type hints for better IDE support
- Comprehensive docstrings
- Proper error handling
- Structured logging

### Testing the API

**Using curl:**
```bash
# Main endpoint
curl http://localhost:8000/

# Health check
curl http://localhost:8000/health

# Check HTTP status code
curl -o /dev/null -s -w "%{http_code}" http://localhost:8000/health
```

**Using HTTPie:**
```bash
http http://localhost:8000/
http http://localhost:8000/health
```

**Using the interactive docs:**
Navigate to http://localhost:8000/docs and use the "Try it out" button on each endpoint.

## License

This project is created for educational purposes as part of a DevOps course.

## Next Steps

This service will evolve throughout the course:
- **Lab 2:** Docker containerization with multi-stage builds
- **Lab 3:** Unit testing and CI/CD pipeline
- **Lab 8:** Prometheus metrics endpoint
- **Lab 9:** Kubernetes deployment with health probes
