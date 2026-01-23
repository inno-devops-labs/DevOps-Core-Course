# DevOps Info Service

## Overview

The DevOps Info Service is a RESTful web application built with Flask that exposes system information, runtime metrics, and health status. It's designed to be lightweight, configurable, and production-ready, with proper error handling, logging, and documentation.

## Prerequisites

- **Python 3.11+**
- **pip** (Python package installer)
- **virtualenv** (recommended for isolated environments)

## Installation

1. **Clone the repository** (if applicable):
   ```bash
   git clone <repository-url>
   cd app_python
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### Basic Usage

Run the application with default settings (listens on `0.0.0.0:5000`):

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

### Verify Installation

Once the application is running, test the endpoints:

```bash
# Main endpoint
curl http://localhost:5000/

# Health check
curl http://localhost:5000/health

# Pretty-printed JSON (requires jq)
curl http://localhost:5000/ | jq
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
    "platform": "Linux",
    "platform_version": "Linux-6.8.0-58-generic-x86_64-with-glibc2.39",
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

### `GET /health`

Returns health status for monitoring and Kubernetes probes.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T14:30:00.000Z",
  "uptime_seconds": 3600
}
```

**Status Codes:**
- `200 OK` - Service is healthy

## Configuration

The application can be configured using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Host address to bind to |
| `PORT` | `5000` | Port number to listen on |
| `DEBUG` | `False` | Enable debug mode (set to `true` to enable) |

### Examples

```bash
# Development (localhost only)
HOST=127.0.0.1 PORT=3000 python app.py

# Production (all interfaces)
HOST=0.0.0.0 PORT=8080 python app.py

# Debug mode
DEBUG=true python app.py
```

## Project Structure

```
app_python/
├── app.py                    # Main application
├── requirements.txt          # Dependencies
├── .gitignore               # Git ignore rules
├── README.md                # This file
├── tests/                   # Unit tests (Lab 3)
│   └── __init__.py
└── docs/                    # Lab documentation
    ├── LAB01.md            # Lab submission
    └── screenshots/        # Proof of work
```

## Development

### Code Style

This project follows PEP 8 style guidelines. Key practices:
- 4 spaces for indentation
- Maximum line length of 79 characters (soft limit 99)
- Clear function and variable names
- Docstrings for functions
- Proper import organization

### Logging

The application uses Python's `logging` module with INFO level by default. Logs include:
- Application startup
- Request information (method, path, client IP)
- Error details

### Error Handling

The application includes error handlers for:
- `404 Not Found` - Invalid endpoints
- `500 Internal Server Error` - Unexpected errors

All errors return JSON responses for consistency.

