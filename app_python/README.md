# DevOps Info Service (Flask)

[![Python CI & Docker Build](https://github.com/hololotl/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)](https://github.com/hololotl/DevOps-Core-Course/actions/workflows/python-ci.yml)


## Overview

A lightweight Flask web service providing detailed information about itself and its runtime environment. Exposes system metrics, runtime statistics, and request metadata via JSON endpoints. Foundation for DevOps monitoring and containerization labs.

## Prerequisites

- Python 3.11+
- pip

## Installation

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the Application

```bash
python app.py                    # Default: 0.0.0.0:5000
PORT=8080 python app.py          # Custom port
HOST=127.0.0.1 PORT=3000 python app.py
```

## Docker

### Building the Image

```bash
docker build -t devops-app:1.0.0 .
```

### Running a Container

```bash
docker run -d -p 5000:5000 devops-app:1.0.0
```

Access the service at `http://localhost:5000`

### Pulling from Docker Hub

```bash
docker pull netotveto/devops-app:1.0.0
docker run -d -p 5000:5000 netotveto/devops-app:1.0.0
```

**Docker Hub Repository:** https://hub.docker.com/r/netotveto/devops-app

### Configuration in Docker

Environment variables can be passed at runtime:

```bash
docker run -d -p 5000:5000 \
  -e HOST=0.0.0.0 \
  -e PORT=5000 \
  -e DEBUG=False \
  devops-app:1.0.0
```

### Dockerfile Features

- **Non-root user**: Runs as `appuser` (uid 1000) for security
- **Multi-stage build**: Optimized image size with separate builder stage
- **Health check**: Included for Kubernetes and orchestration readiness
- **Specific base image**: Python 3.13-slim for smaller footprint
- **.dockerignore**: Excludes unnecessary files for faster builds

For detailed implementation documentation, see [LAB02.md](docs/LAB02.md)

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service and system information (JSON) |
| `/health` | GET | Health check — returns status 200 if healthy |
| `/metrics` | GET | Prometheus metrics endpoint |

## Metrics (Prometheus)

The service now exports Prometheus-compatible metrics for monitoring:

- `http_requests_total{method, endpoint, status_code}` — total number of HTTP requests
- `http_request_duration_seconds{method, endpoint, status_code}` — request duration histogram
- `http_requests_in_progress{method, endpoint}` — currently active requests gauge
- `devops_info_endpoint_calls_total{endpoint}` — app-specific endpoint call counter
- `devops_info_system_collection_seconds` — system info collection duration histogram

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `5000` | Bind port |
| `DEBUG` | `False` | Enable Flask debug mode |

Example:
```bash
HOST=127.0.0.1 PORT=3000 DEBUG=True python app.py
```
