# DevOps Info Service

## Overview
A Python-based web service designed to furnish details about itself and its operational environment. This service serves as a foundation for subsequent experiments in containerization, continuous integration and continuous deployment (CI/CD), monitoring, and deployment processes.

## Prerequisites
- Python 3.11 or higher
- pip (Python Package manager)

## Installation
1. Clone repository:
```bash
# Clone the project
git clone https://github.com/s3rap1s/DevOps-Core-Course.git
cd DevOps-Core-Course/app_python

# Create virtual environment
python3 -m venv venv
source venv/bin/activate # on Linux / macOs or .\venv\Scripts\Activate.ps1 on windows

# Install dependencies
pip install -r requirements.txt
```

## Running the Application

```bash
# Default configuration
python app.py

# With custom port
PORT=8080 python app.py

# With custom port and host
HOST=127.0.0.1 PORT=3000 python app.py
```

## API Endpoints

### `GET /`
Return comprehensive service and system information:

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

### `GET /health`

Simple health endpoint for monitoring:

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T14:30:00.000Z",
  "uptime_seconds": 3600
}
```


## Configuration

| Variable | Default   | Description                  |
| -------- | --------- | ---------------------------- |
| `HOST`   | `0.0.0.0` | Network interface to bind    |
| `PORT`   | `5000`    | Port to listen on            |
| `DEBUG`  | `false`   | Enable debug mode            |
