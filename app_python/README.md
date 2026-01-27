# DevOps Info Service

A production-ready Python web service that provides comprehensive information about itself and its runtime environment.

## Overview

The DevOps Info Service is a RESTful API that returns detailed system information, health status, and service metadata. This service serves as a foundation for learning DevOps practices including containerization, CI/CD, monitoring, and orchestration.

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)

## Installation

1. Clone the repository and navigate to the app_python directory:
```bash
cd app_python
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:

On macOS/Linux:
```bash
source venv/bin/activate
```

On Windows:
```bash
venv\Scripts\activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

### Default Configuration
```bash
python app.py
```
The service will start on `http://0.0.0.0:5000`

### Custom Configuration
```bash
# Custom port
PORT=8080 python app.py

# Custom host and port
HOST=127.0.0.1 PORT=3000 python app.py

# Enable debug mode
DEBUG=True python app.py
```

## API Endpoints

### GET /

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
    {"path": "/health", "method": "GET", "description": "Health check"}
  ]
}
```

### GET /health

Simple health check endpoint for monitoring and Kubernetes probes.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T14:30:00.000Z",
  "uptime_seconds": 3600
}
```

## Configuration

The application can be configured via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Host to bind the server to |
| `PORT` | `5000` | Port number for the server |
| `DEBUG` | `False` | Enable debug mode |

## Examples

### Testing with curl
```bash
# Main endpoint
curl http://localhost:5000/

# Health check
curl http://localhost:5000/health

# Pretty print JSON
curl http://localhost:5000/ | jq
```

### Testing with Python
```bash
python -c "import requests; print(requests.get('http://localhost:5000/').json())"
```

## Project Structure

```
app_python/
├── app.py                    # Main application
├── requirements.txt          # Dependencies
├── .gitignore               # Git ignore
├── README.md                # This file
├── tests/                   # Unit tests
│   └── __init__.py
└── docs/                    # Lab documentation
    ├── LAB01.md            # Lab submission
    └── screenshots/        # Proof of work
```

## Best Practices Implemented

- Clean code organization with clear function names
- Proper imports grouping
- Error handling for 404 and 500 errors
- Structured logging
- PEP 8 compliant code
- Environment variable configuration
- Comprehensive documentation

## Future Enhancements

This service will evolve throughout the DevOps course:
- **Lab 2:** Containerization with Docker
- **Lab 3:** Unit tests and CI/CD pipeline
- **Lab 8:** Prometheus metrics endpoint
- **Lab 9:** Kubernetes deployment
- **Lab 12:** Persistent storage with visit counter
- **Lab 13:** GitOps with ArgoCD

## License

Educational use for DevOps course.
