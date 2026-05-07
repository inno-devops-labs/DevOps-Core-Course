# DevOps Info Service (Python)

![Python CI](https://github.com/pop-arthur/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)

[![Docker Hub](https://img.shields.io/docker/v/poparthur/devops-info-service?label=docker&logo=docker)](https://hub.docker.com/r/poparthur/devops-info-service)

A FastAPI-based web service that provides system information, runtime metrics, and health monitoring. Built as part of the DevOps course.

## Overview

This web service offers endpoints that provide detailed information about the service and the system it runs on, including:
- runtime metrics
- request details
- health status
## Prerequisites

- Python 3.11+ 
- pip

## Installation

```bash
# Navigate to project directory
cd DevOps-Course/lab01/app_python

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Application

**Default (0.0.0.0:5000):**
```bash
python app.py
```

**Custom configuration:**
```bash
PORT=8080 python app.py
HOST=127.0.0.1 PORT=3000 python app.py
DEBUG=true PORT=8080 python app.py
```

**Development with auto-reload:**
```bash
uvicorn app:app --reload
```

## API Endpoints

### `GET /`
Returns comprehensive service and system information.

```bash
curl http://localhost:5000/
```

**Response includes:**
- Service metadata (name, version, framework)
- System info (hostname, platform, architecture, CPU count, Python version)
- Runtime metrics (uptime, current time, timezone)
- Request details (client IP, user agent, method, path)
- Available endpoints

### `GET /health`
Health check endpoint for monitoring tools.

```bash
curl http://localhost:5000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-26T07:32:24.854178+00:00",
  "uptime_seconds": 42
}
```

### Interactive Documentation

- **Swagger UI:** http://localhost:5000/docs

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `5000` | Server port number |
| `DEBUG` | `False` | Enable debug mode |

## Testing

```bash
# Test endpoints
curl http://localhost:5000/
curl http://localhost:5000/health

# Pretty-print JSON
curl -s http://localhost:5000/ | python3 -m json.tool
```

## Troubleshooting

**Port already in use:**
```bash
PORT=8080 python app.py
# Or find and kill the process: lsof -i :5000
```

**Module not found:**
```bash
pip install -r requirements.txt
```

## Project Structure

```
app_python/
├── app.py                 # Main application
├── requirements.txt       # Dependencies
├── README.md             # This file
├── tests/                # Unit tests
└── docs/                 # Documentation
    ├── LAB01.md         # Lab report
    └── screenshots/     # Evidence
```

### Docker Container 

**Build the image locally:**
```bash
docker build -t [your-image-name] .
docker build -t devops-service:latest .
docker build -t my-org/devops-service:v1.0 .
```

**Run a container:**
```bash
# Basic run with port mapping
docker run -p [host-port]:5000 [image-name]

# Examples:
docker run -p 5000:5000 devops-service
docker run -p 8080:5000 devops-service:latest
docker run -d -p 5000:5000 --name my-service devops-service
```

**With environment variables:**
```bash
docker run -p 5000:5000 -e PORT=5000 -e DEBUG=true [image-name]
```

**Pull from Docker Hub:**
```bash
# Pull the public image
docker pull poparthur/devops-info-service:latest 

# Run the pulled image
docker run -p [host-port]:5000  poparthur/devops-info-service:latest 

# Pull specific version
docker pull  poparthur/devops-info-service:latest :[tag]
```

## Docker Hub Repository

The application is available on Docker Hub:
- **Image:** ` poparthur/devops-info-service:latest`
- **Tags:** `latest`
- **URL:** https://hub.docker.com/r/poparthur/devops-info-service

Pull and run with:
```bash
docker pull arthurdevops/devops-service:latest
docker run -p 5000:5000 arthurdevops/devops-service:latest
```

## How to Run Tests

Ensure you have installed `pytest` and `httpx` libs and run:

```bash
# Run all tests
pytest

# Run specific file
pytest tests/test_endpoints.py 

# Run specific test
pytest tests/test_endpoints.py::test_various_nonexistent_paths
```