[![Python CI](https://github.com/newspec/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg?branch=lab03)](https://github.com/newspec/DevOps-Core-Course/actions/workflows/python-ci.yml?query=branch%3Alab03)

# devops-info-service

## Overview
`devops-info-service` is a lightweight HTTP service built with **FastAPI** that returns comprehensive runtime and system information. It exposes:
- service metadata (name, version, description, framework),
- system details (hostname, OS/platform, architecture, CPU count, Python version),
- runtime data (uptime, current UTC time),
- request details (client IP, user-agent, method, path),
- a list of available endpoints.

## Prerequisites
- **Python:** 3.10+ (recommended 3.11+)
- **Dependencies:** listed in `requirements.txt`

## Installation

```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the Application
```
python app.py
# Or with custom config
PORT=8080 python app.py
```

## API Endpoints
- `GET /` - Service and system information
- `GET /health` - Health check

## Configuration

The application is configured using environment variables.

| Variable | Default | Description | Example     |
|---------|---------|-------------|-------------|
| `HOST`  | `0.0.0.0` | Host interface to bind the server to | `127.0.0.1` |
| `PORT`  | `8000` | Port the server listens on | `8080`      |

# Docker

## Building the image locally
Command pattern:
```bash
docker build -t <image_name>:<tag> <path_to_app>
```

## Running a container
Command pattern:
```bash
docker run --rm -p <host_port>:<container_port> <image_name>:<tag>
```

## Pulling from Docker Hub
Command pattern:
```bash
docker pull <dockerhub_username>/<repo_name>:<tag>
```
Then run:
```bash
docker run --rm -p <host_port>:<container_port> <dockerhub_username>/<repo_name>:<tag>
```

# Testing
To run test locally use command:
```bash
pytest
```
