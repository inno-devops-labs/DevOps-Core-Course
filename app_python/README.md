[![Python CI](https://github.com/newspec/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg?branch=lab03)](https://github.com/newspec/DevOps-Core-Course/actions/workflows/python-ci.yml?query=branch%3Alab03)
[![Coverage](https://codecov.io/gh/newspec/DevOps-Core-Course/branch/lab03/graph/badge.svg?flag=python)](https://codecov.io/gh/newspec/DevOps-Core-Course/branch/lab03?flag=python)


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
- `GET /` - Service and system information (also increments visit counter)
- `GET /health` - Health check
- `GET /visits` - Current visit count

## Configuration

The application is configured using environment variables.

| Variable | Default | Description | Example |
|---------|---------|-------------|---------|
| `HOST` | `0.0.0.0` | Host interface to bind the server to | `127.0.0.1` |
| `PORT` | `8000` | Port the server listens on | `8080` |
| `VISITS_FILE` | `/data/visits` | Path to the visits counter file | `/tmp/visits` |

## Visits Counter

Each request to `GET /` increments a persistent counter stored in `VISITS_FILE` (default: `/data/visits`).
The counter survives container restarts when the data directory is mounted as a volume.

```
GET /  →  read counter  →  increment  →  write back  →  return response with visits
GET /visits  →  read counter  →  return {"visits": N}
```

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

## Running with Docker Compose (with persistent visits counter)

```bash
# Start the application with a persistent data volume
docker compose up -d

# Access the root endpoint (increments counter)
curl http://localhost:8000/

# Check the visit count
curl http://localhost:8000/visits

# Inspect the counter file on the host
cat ./data/visits

# Restart the container and verify counter persists
docker compose restart
curl http://localhost:8000/visits
```

The `docker-compose.yml` mounts `./data` on the host to `/app/data` inside the container,
so the visits file survives container restarts.

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

