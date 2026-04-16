# DevOps Info Service (Lab 1)

## Overview

This project implements a simple **DevOps info service** written in Python using **Flask**. The service exposes HTTP endpoints that return detailed information about the application, the underlying system, and its runtime health. It is the base for later labs (Docker, CI/CD, monitoring, persistence, etc.).

## Prerequisites

- Python 3.11+ (recommended)
- pip (Python package manager)
- Optional: `virtualenv` or `venv` for isolated environments

## Installation

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env_example .env      # create local env file from example
```

## Running the Application

```bash
# Default configuration (HOST=0.0.0.0, PORT=5002, DEBUG=False)
python app.py

# Custom configuration via environment variables
PORT=8080 python app.py
HOST=127.0.0.1 PORT=3000 DEBUG=true python app.py
```

## API Endpoints

- `GET /` – Service and system information
  - Service metadata (name, version, description, framework)
  - External configuration loaded from `CONFIG_PATH`
  - System info (hostname, platform, architecture, CPU count, Python version)
  - Runtime info (uptime, current time, timezone)
  - Persisted visits counter and storage path
  - Request info (client IP, user agent, HTTP method, path)
  - List of available endpoints

- `GET /health` – Health check
  - Returns basic health status, timestamp, and uptime in seconds

- `GET /ready` – Readiness check
  - Returns readiness status, timestamp, and uptime in seconds

- `GET /metrics` – Prometheus metrics endpoint
  - Exposes RED metrics:
    - `http_requests_total{method,endpoint,status_code}`
    - `http_request_duration_seconds{method,endpoint,status_code}`
    - `http_requests_in_progress{method,endpoint}`
  - Exposes app-specific metrics:
    - `devops_info_endpoint_calls{endpoint}`
    - `devops_info_system_collection_seconds`

- `GET /visits` – Persisted visits counter
  - Returns the current count stored in `VISITS_FILE`
  - Does not increment the counter

## Configuration

Configuration is done via environment variables:

| Variable | Default | Description |
|---------|---------|-------------|
| `HOST` | `0.0.0.0` | Address the Flask app listens on |
| `PORT` | `5002` | TCP port for HTTP server |
| `DEBUG` | `False` | Enable Flask debug mode if `true` |
| `CONFIG_PATH` | `/config/config.json` | JSON config file loaded at request time |
| `VISITS_FILE` | `/data/visits` | File used to persist the visit counter |

All configuration is read in `app.py` at startup, so restart the application after changing environment variables.

The JSON config file is optional. If `CONFIG_PATH` does not exist, the application still starts and returns an empty `configuration.config_file` object.

## Persistence

The root endpoint increments a file-backed counter on every request. The counter is persisted in `VISITS_FILE` using an atomic write (`os.replace`) and a process-local lock so the file contents remain consistent during concurrent requests handled by the same container.

Quick local check without Docker:

```bash
mkdir -p data
VISITS_FILE=./data/visits python app.py
curl -s http://127.0.0.1:5002/ | jq '.visits'
curl -s http://127.0.0.1:5002/ | jq '.visits'
curl -s http://127.0.0.1:5002/visits | jq
cat ./data/visits
```

## Docker Compose Persistence Test

Run the container with a bind mount so the counter survives container recreation:

```bash
docker compose up --build -d
curl -s http://127.0.0.1:5002/ | jq '.visits'
curl -s http://127.0.0.1:5002/ | jq '.visits'
cat ./data/visits
docker compose down
docker compose up -d
curl -s http://127.0.0.1:5002/visits | jq
```

Expected result:

- `./data/visits` increases with each `GET /`
- after `docker compose down` and `docker compose up -d`, `GET /visits` returns the previously stored value

## Structured Logging (Lab 7)

The service writes JSON logs to `stdout` for centralized log collection (Loki/Promtail).

Example:

```json
{"timestamp":"2026-03-12T20:45:10.123456+00:00","level":"INFO","logger":"devops-info-service","message":"HTTP request handled","method":"GET","path":"/health","status_code":200,"client_ip":"127.0.0.1","duration_ms":1.11}
```

Each request log includes:

- `method`
- `path`
- `status_code`
- `client_ip`
- `duration_ms`
- `user_agent`

## Docker

How to use the containerized application (patterns):

- **Build image (local):** `docker build -t <local-name>:<tag> <path-to-app-python>`
- **Tag for Docker Hub:** `docker tag <local-name>:<tag> <username>/<repo>:<tag>`
- **Run container (local):** `docker run -p <host-port>:<container-port> --name <container-name> <image>`
- **Pull from Docker Hub:** `docker pull <username>/<repo>:<tag>`

Notes:
- The container exposes port `5002` by default (see `app.py`).
- The image runs as a non-root user for improved security.
