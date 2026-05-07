# Overview
This service is a Flask-based study service in python that returns comprehensive service and system information. It provides endpoints for service metadata, system statistics, and health monitoring, making it useful for DevOps monitoring and system diagnostics.

# Prerequisites
- **Python Version**: 3.8 or higher
- **Dependencies** (from requirements.txt):
  - Flask==3.1.0

# Installation
1. **Clone the repository**:
2. **Create and activate a virtual environment**:
```bash
python -m venv venv
source venv/bin/activate
```
3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

# Running the Application
```
python app.py
# Or with custom config
PORT=8080 python app.py
HOST=127.0.0.1 PORT=3000 python app.py
```

# API Endpoint
## `GET /` - Service and system information
### Example Response:
```
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

## `GET /health` - Health check
### Example Response:
```
{
  "status": "healthy",
  "timestamp": "2024-01-15T14:30:00.000Z",
  "uptime_seconds": 3600
}
```

## `GET /ready` - Health check
### Example Response:
```
{
  "status": "ready",
}
```

## `GET /visits` - Health check
### Example Response:
```
{
  "visits": 1,
}
```

# Configuration 
| Variable name | Basic value | Description |
|----------|--------|-------------|
| **Host** | 0.0.0.0 | IP of the service |
| **Port** | 5000 | Port of the service |
| **Debug** | False | Debug mode enabeled |

# Docker
This application is containerized and ready for deployment using Docker.

## Building the Image Locally
To build the Docker image from source:
```sh
# Navigate to the application directory
cd app

# Build the image with a tag
docker build -t <image-name>:<tag> .
```

## Running the Container
To run the application in a container:
```sh
# Basic run with port mapping
docker run -d -p <host-port>:<container-port> <image-name>:<tag>
```

## Pulling from Docker Hub
The image is available on Docker Hub and can be pulled directly:
```sh
# Pull the latest version
docker pull <dockerhub-username>/<image-name>:latest
```


# GitHub Actions Status Badge
[![Python test and build](https://github.com/SamuelAnton/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg?branch=lab03)](https://github.com/SamuelAnton/DevOps-Core-Course/actions/workflows/python-ci.yml)

# Testing
To test locally run
```sh
cd app_python
pytest .
```