# DevOps Info Service - Python

A production-ready web service that provides comprehensive information about itself and its runtime environment. Built with Flask framework.

## Overview

The DevOps Info Service is a RESTful API that exposes system information, runtime metrics, and health status. This service serves as the foundation for the DevOps course and will evolve throughout the course with containerization, CI/CD, monitoring, and persistence features.

**Key Features:**
- System information endpoint (`GET /`)
- Health check endpoint (`GET /health`)
- Configurable via environment variables
- Production-ready error handling and logging

## Prerequisites

- **Python:** 3.11 or higher
- **pip:** Python package manager
- **Virtual environment:** Recommended for dependency isolation

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd DevOps-Core-Course/app_python
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   ```bash
   # On macOS/Linux:
   source venv/bin/activate
   
   # On Windows:
   venv\Scripts\activate
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### Basic Usage

Run the application with default settings (host: `0.0.0.0`, port: `5001`):

```bash
python app.py
```

### Custom Configuration

Configure the application using environment variables:

```bash
# Custom port
PORT=8080 python app.py

# Custom host and port
HOST=127.0.0.1 PORT=3000 python app.py

# Enable debug mode
DEBUG=true python app.py
```

The service will be available at `http://<HOST>:<PORT>`

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
    "platform_version": "25.2.0",
    "architecture": "arm64",
    "cpu_count": 8,
    "python_version": "3.13.1"
  },
  "runtime": {
    "uptime_seconds": 3600.5,
    "uptime_human": "1 hour, 0 minutes, 0 seconds",
    "current_time": "2026-01-31T17:30:00.000Z",
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

**Example Request:**
```bash
curl http://localhost:5001/
```

### `GET /health`

Simple health check endpoint for monitoring and Kubernetes probes.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-31T17:30:00.000Z",
  "uptime_seconds": 3600.5
}
```

**Status Codes:**
- `200 OK`: Service is healthy

**Example Request:**
```bash
curl http://localhost:5001/health
```

## Configuration

The application can be configured using the following environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Host address to bind the server |
| `PORT` | `5001` | Port number to listen on |
| `DEBUG` | `False` | Enable debug mode (set to `true` to enable) |

## Project Structure

```
app_python/
├── app.py                    # Main application
├── requirements.txt          # Python dependencies
├── .gitignore               # Git ignore rules
├── README.md                # This file
├── tests/                   # Unit tests (for Lab 3)
│   └── __init__.py
└── docs/                    # Documentation
    ├── LAB01.md            # Lab submission documentation
    └── screenshots/        # Screenshots and proof of work
```

## Dependencies

- **Flask 3.1.0** - Lightweight web framework

See `requirements.txt` for pinned versions.

## Development

### Testing

Test the endpoints using curl:

```bash
# Test main endpoint
curl http://localhost:5001/ | jq

# Test health endpoint
curl http://localhost:5001/health | jq
```

Or use a browser to visit:
- `http://localhost:5001/`
- `http://localhost:5001/health`

