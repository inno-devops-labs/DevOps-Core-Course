# DevOps Info Service

[![python-ci](https://github.com/gghost1/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg?branch=lab03)](https://github.com/gghost1/DevOps-Core-Course/actions/workflows/python-ci.yml)
[![codecov](https://codecov.io/gh/gghost1/DevOps-Core-Course/branch/lab03/graph/badge.svg)](https://codecov.io/gh/gghost1/DevOps-Core-Course)

## Overview
A simple Python web service that returns service info, system information, runtime uptime, and request details.

## Prerequisites
- Python 3.10+ (recommended: latest available in your environment)
- pip + virtualenv

## Installation
```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

## Running the Application
```bash
python3 app.py
```
Custom config:
```bash
PORT=8080 python3 app.py
# or
HOST=127.0.0.1 PORT=3000 DEBUG=true python3 app.py
```
Production-like run (WSGI):
```bash
gunicorn -w 2 -b 0.0.0.0:5000 app:app
```

## API Endpoints
- GET `/` — Service and system information
- GET `/visits` — Current persisted visits count
- GET `/health` — Health check

## Configuration
| Variable            | Default                    | Description         |
| ------------------- | -------------------------- | ------------------- |
| HOST                | 0.0.0.0                    | Bind address        |
| PORT                | 5000                       | Listen port         |
| DEBUG               | false                      | Flask debug mode    |
| LOG_LEVEL           | INFO                       | Logging level       |
| SERVICE_NAME        | devops-info-service        | Service name        |
| SERVICE_VERSION     | 1.0.0                      | Service version     |
| SERVICE_DESCRIPTION | DevOps course info service | Service description |
| VISITS_FILE         | /data/visits               | Path to visits file |

## Testing
Install dev dependencies:
```bash
pip3 install -r requirements.txt -r requirements-dev.txt
```

### Run tests:
```bash
pytest
```

### Lint/format check:
```bash
ruff check .
ruff format --check .
```

## Docker
### Build image (local)
From the `app_python/` directory, build an image using the current folder as the build context:
```bash
docker build -t <image-name>:<tag> .
```

### Run container
Run the container with port publishing so the service is reachable from the host:
```bash
docker run --rm -p <host-port>:<container-port> gghost1/devops-lab-app-python:latest
```
Pass configuration via environment variables (the app reads HOST, PORT, DEBUG):
```bash
docker run --rm -e PORT=<port> -p <port>:<port> gghost1/devops-lab-app-python:latest
```
For local built image replace `gghost1/devops-lab-app-python:latest` on your `<image-name>:<tag>`.

### Pull from Docker Hub
Pull an already published image from Docker Hub:
```bash
docker pull gghost1/devops-lab-app-python:latest
```

### Docker Compose
Run with bind-mounted storage:
```bash
docker compose up -d --build
```