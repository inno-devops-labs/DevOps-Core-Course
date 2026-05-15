# DevOps Info Service

[![Python CI](https://github.com/LocalT0aster/DevOps-Core-S26/actions/workflows/python-ci.yml/badge.svg)](https://github.com/LocalT0aster/DevOps-Core-S26/actions/workflows/python-ci.yml)

## Overview

Small Flask web service that reports service metadata, system information, runtime uptime, and basic request details. Includes a persistent visits counter stored at `/data/visits`, plus health, readiness, and Prometheus metrics endpoints for monitoring.

## Prerequisites

- Python 3.14+
- uv

## Installation

```bash
uv sync --locked
```

`uv.lock` is the source of truth for Python dependencies. `requirements.txt` is generated from it for Snyk's pip-compatible scan path and should be refreshed with:

```bash
uv export --locked --no-dev --no-annotate --no-header --no-hashes --format requirements.txt --output-file requirements.txt > /dev/null
```

### Docker

- Pull the container:
  ```bash
  docker pull localt0aster/devops-app-py
  ```
- OR build the container yourself:
  ```bash
  docker build -t localt0aster/devops-app-py .
  ```
  The Docker build installs dependencies with:
  ```bash
  uv sync --locked --no-dev --no-install-project
  ```
  The image uses the pinned uv binary image and runs as `appuser` with `HOME=/home/appuser`.

## Running the Application

Production-style local run with Gunicorn:

```bash
uv run gunicorn --config gunicorn.conf.py src.main:app
HOST=127.0.0.1 PORT=8080 uv run gunicorn --config gunicorn.conf.py src.main:app
```

Gunicorn access logs are emitted as JSON so Loki can parse request fields cleanly.

### Docker

- Run the container:
  ```bash
  docker run -p 5000:5000 -e HOST="0.0.0.0" -d localt0aster/devops-app-py
  ```

## API Endpoints

- `GET /` - Service and system information
- `GET /visits` - Current persisted visit counter
- `GET /health` - Health check
- `GET /ready` - Readiness check
- `GET /metrics` - Prometheus metrics exposition

## Visits Counter

- The root handler increments the counter on every `GET /`.
- The counter is persisted as plain text in `/data/visits`.
- If the file is missing, the service starts from `0`.
- If the file is malformed, empty, or negative, the service logs a warning and treats the value as `0`.

## Local Docker Check

For Lab 12, run the monitoring stack with a writable `/data` volume for the Python container and verify that:

- repeated `GET /` calls increment the counter
- `GET /visits` returns the current count
- the counter survives a container restart because the backing file is persisted on the host

## Configuration

| Variable | Default   | Description                              |
| -------- | --------- | ---------------------------------------- |
| `HOST`   | `0.0.0.0` | Bind address for the server              |
| `PORT`   | `5000`    | Port to listen on                        |
| `DEBUG`  | `False`   | Enable Flask debug mode (`true`/`false`) |

## Testing

The project uses `pytest` for unit tests.

```bash
uv sync --locked
uv run pytest --cov=src --cov-report=term-missing
```

The test suite covers:

- `GET /` response schema and visits counter increment behavior
- `GET /visits` bootstrap, persisted reads, and malformed-file fallback
- `GET /health` successful response schema and types
- `404` JSON error handling for unknown routes
- `500` JSON error handling for simulated internal failures

## Linting

```bash
uv run flake8 src tests
```
