# DevOps Info Service

A production-ready web service providing detailed information about itself and its runtime environment. Built with FastAPI for high performance and automatic API documentation.

## Overview

The DevOps Info Service is a FastAPI-based web application  that reports comprehensive system information, runtime statistics, and service metadata. This service serves as the foundation for a monitoring tool that will evolve throughout the DevOps course.

**Features:**
- System information (hostname, platform, architecture, CPU count, Python version)
- Runtime statistics (uptime, current time, timezone)
- Request metadata (client IP, user agent, method, path)
- Health check endpoint for monitoring


## Prerequisites

- **Python 3.11+** (Python 3.12+ recommended)
- pip: package manager
- Operating System: Windows/macOS/Linux

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
   
   On Windows:
   ```bash
   venv\Scripts\activate
   ```
   
   On Linux/Mac:
   ```bash
   source venv/bin/activate
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### Basic Usage

Run the application with default settings (host: `0.0.0.0`, port: `5000`):

```bash
python app.py
```

The service will be available at http://localhost:5000

### Custom Configuration

Configure the application using environment variables:

```bash
# Custom port
PORT=8080 python app.py

# Custom host and port
HOST=127.0.0.1 PORT=3000 python app.py

# Enable debug mode
DEBUG=True python app.py
```

### Using Uvicorn Directly

You can also run the application directly with uvicorn:

```bash
uvicorn app:app --host 0.0.0.0 --port 5000
```

## API Endpoints

### `GET /`

Returns comprehensive service and system information.


- service: service metadata (name, version, description, framework)

- system: information about system (hostname, platform, architecture, CPU count, Python version)

- runtime: runtime metrics (uptime, current time, timezone)

- request: details of request (client IP, user agent, method, path)

- endpoints: available API endpoints

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
    "platform_version": "Linux-5.15.0-91-generic-x86_64-with-glibc2.35",
    "architecture": "x86_64",
    "cpu_count": 8,
    "python_version": "3.12.1"
  },
  "runtime": {
    "uptime_seconds": 3600,
    "uptime_human": "1 hour, 0 minutes",
    "current_time": "2026-01-28T14:30:00.000000+00:00",
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

**Testing:**
```bash
curl http://localhost:5000/
```

### `GET /health`

Simple health check endpoint for monitoring and Kubernetes liveness/readiness probes.

**Response Example:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T14:30:00.000000+00:00",
  "uptime_seconds": 3600
}
```

**HTTP Status:** 200 OK

**Testing:**
```bash
curl http://localhost:5000/health
```

## Configuration

The application can be configured using the following environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Host address to bind the server |
| `PORT` | `5000` | Port number to listen on |
| `DEBUG` | `False` | Enable debug mode  |

### Examples

```bash
# Development with custom port
PORT=8080 DEBUG=True python app.py

# Production with specific host
HOST=0.0.0.0 PORT=80 python app.py
```

## Development

### Project Structure

```
app_python/
├── app.py              # Main application
├── requirements.txt    # Python dependencies
├── .gitignore         # Git ignore rules
├── README.md          # This file
├── tests/             # Unit tests (Lab 3)
│   └── __init__.py
└── docs/              # Documentation
    ├── LAB01.md       # Lab submission
    └── screenshots/   # Screenshots
```


## Testing

Test the endpoints using curl, HTTPie, or any HTTP client:

```bash
# Main endpoint
curl http://localhost:5000/ | jq

# Health check
curl http://localhost:5000/health | jq

# Pretty print output
curl -s http://localhost:5000/ | python -m json.tool
```

## Troubleshooting

**Port already in use:**
```bash
# Use a different port
PORT=8080 python app.py
```

**Module not found errors:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate
# Reinstall dependencies
pip install -r requirements.txt
```



