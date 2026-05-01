# DevOps Info Service

## Overview
A Python-based web service designed to furnish details about itself and its operational environment. This service serves as a foundation for subsequent experiments in containerization, continuous integration and continuous deployment (CI/CD), monitoring, and deployment processes.

## CI/CD Pipeline
![Python CI/CD](https://github.com/s3rap1s/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)

### Overview
This project uses GitHub Actions for continuous integration and deployment. The pipeline includes:

1. **Code Quality Checks**
   - Linting with flake8
   - Code formatting with black
   - Security scanning with Snyk

2. **Testing**
   - Unit tests with pytest
   - Test coverage tracking
   - 90%+ code coverage requirement

3. **Docker Build & Deployment**
   - Multi-stage Docker builds
   - Automated tagging with Calendar Versioning
   - Push to Docker Hub

### Versioning Strategy
We use **Calendar Versioning (CalVer)** with the format `YYYY.MM.MICRO`:

- **YYYY.MM.DD** - Specific date of build
- **YYYY.MM.MICRO** - Version with micro release number
- **latest** - Most recent stable build


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

# With custom data and config paths
DATA_DIR=./data CONFIG_FILE=./config/config.json python app.py
```

## Testing the Application
```bash
pytest  # Run all tests
pytest --cov=app --cov-report=term-missing  # Run with coverage
```

## Docker

This application is containerized and available as a Docker image.

### Building the Image Locally

```bash
docker build -t devops-info-service:latest .
```

### Running a Container

```bash
# Run with default port mapping
docker run -d -p 5000:5000 devops-info-service:latest

# Run with custom port
docker run -d -p 8080:5000 devops-info-service:latest

# Run with environment variables
docker run -d -p 3000:3000 -e PORT=3000 -e HOST=0.0.0.0 devops-info-service:latest

# Run with persistent visits storage
docker run -d -p 5000:5000 \
  -e DATA_DIR=/app/data \
  -v devops-info-service-data:/app/data \
  devops-info-service:latest
```

### Pulling from Docker Hub

```bash
# Pull the latest version
docker pull your-username/devops-info-service:latest

# Run pulled image
docker run -d -p 5000:5000 your-username/devops-info-service:latest
```

### Environment Variables in Docker
When running in Docker, you can pass environment variables using the `-e` flag:

```bash
docker run -d -p 5000:5000 \
  -e HOST=0.0.0.0 \
  -e PORT=5000 \
  -e DEBUG=false \
  devops-info-service:latest
```

## API Endpoints

### `GET /`
Return comprehensive service and system information:

```json
{
  "service": {
    "name": "devops-info-service",
    "version": "2.0.0",
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
    "timezone": "UTC",
    "visits_count": 12
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/7.81.0",
    "method": "GET",
    "path": "/"
  },
  "configuration": {
    "file": {
      "application_name": "devops-info-service",
      "environment": "development",
      "settings": {
        "featureGreeting": true,
        "maxVisitsDisplay": 10
      }
    },
    "environment": {
      "APP_ENV": "development",
      "LOG_LEVEL": "info",
      "FEATURE_GREETINGS": "true",
      "CONFIG_FILE": "/config/config.json",
      "DATA_DIR": "/data"
    }
  },
  "endpoints": [
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/health", "method": "GET", "description": "Health check"},
    {"path": "/visits", "method": "GET", "description": "Visit counter"},
    {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"}
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

### `GET /visits`

Returns the current persisted visit counter:

```json
{
  "visits": 12,
  "file": "/data/visits"
}
```


## Configuration

| Variable | Default   | Description                  |
| -------- | --------- | ---------------------------- |
| `HOST`   | `0.0.0.0` | Network interface to bind    |
| `PORT`   | `5000`    | Port to listen on            |
| `DEBUG`  | `false`   | Enable debug mode            |
| `DATA_DIR` | `./data` | Directory used for visits persistence |
| `VISITS_FILE` | `<DATA_DIR>/visits` | File storing visit counter |
| `CONFIG_FILE` | `./config/config.json` | JSON config file path |

## Persistence

The root endpoint increments a counter stored in the visits file. The `/visits` endpoint returns the current value without incrementing it.

For local Docker Compose testing, the application container mounts a persistent volume to keep `/app/data/visits` across container restarts.
