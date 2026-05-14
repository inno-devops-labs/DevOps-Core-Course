# DevOps Info Service (Python / FastAPI)

[![Python CI](https://github.com/XriXis/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)](https://github.com/XriXis/DevOps-Core-Course/actions/workflows/python-ci.yml)
[![Python CD](https://github.com/XriXis/DevOps-Core-Course/actions/workflows/python-cd.yml/badge.svg)](https://github.com/XriXis/DevOps-Core-Course/actions/workflows/python-cd.yml)

## Overview

DevOps Info Service is a FastAPI application used across the course labs. For Lab 12 it was extended with:

- a persisted visits counter stored in a file
- a `GET /visits` endpoint
- optional file-based configuration loading from `CONFIG_PATH`
- a Docker Compose workflow for local persistence testing

## Tech Stack

- Python 3.14
- FastAPI 0.128.0
- Uvicorn 0.40.0
- Prometheus client 0.23.1

## Project Structure

```text
solution/app_python/
├── app.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── requirements.dev.txt
├── tests/
└── docs/
```

## Run On Host

```bash
cd solution/app_python
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Environment variable examples:

```bash
$env:PORT="8080"; python app.py
$env:DEBUG="true"; python app.py
$env:VISITS_FILE="C:\temp\visits"; python app.py
$env:CONFIG_PATH="C:\temp\config.json"; python app.py
```

## Run Tests

```bash
cd solution/app_python
pip install -r requirements.dev.txt
pytest tests/ -v --cov=. --cov-report=term-missing
```

## Run With Docker

Build and run directly:

```bash
cd solution/app_python
docker build -t devops-info-service:lab12 .
docker run --rm -p 5000:5000 `
  -e VISITS_FILE=/data/visits `
  -v ${PWD}/data:/data `
  devops-info-service:lab12
```

Run with Docker Compose:

```bash
cd solution/app_python
docker compose up --build -d
curl http://localhost:5000/
curl http://localhost:5000/visits
Get-Content .\data\visits
docker compose restart
curl http://localhost:5000/visits
docker compose down
```

The Compose setup mounts `./data` into the container at `/data`, so the visits counter survives container restarts.

## API Endpoints

### `GET /`

Returns service metadata, system information, runtime data, loaded configuration, and the incremented visits counter.

Important behavior:

- every request to `/` increments the persisted counter
- the counter is written to the file defined by `VISITS_FILE`
- the response includes the active config file path and visits file path

### `GET /visits`

Returns the current persisted counter without incrementing it.

Example response:

```json
{
  "count": 5,
  "file_path": "/data/visits"
}
```

### `GET /health`

Returns service health and uptime.

### `GET /metrics`

Returns Prometheus metrics for the service.

## Configuration

Supported environment variables:

| Variable | Default | Description |
| --- | --- | --- |
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `5000` | HTTP port |
| `DEBUG` | `false` | Enables debug logging |
| `RELEASE_VERSION` | `v1` | Release label exposed by the app |
| `VISITS_FILE` | `/data/visits` | Path to the persisted visits counter |
| `CONFIG_PATH` | `/config/config.json` | Path to JSON configuration file |

If `CONFIG_PATH` does not exist, the app falls back to built-in defaults and keeps running.

## Persistence Notes

- the visits counter is initialized to `0` if the file does not exist
- writes are serialized with an in-process lock
- the file is updated using an atomic replace operation to reduce corruption risk
- this storage model is suitable for a single-replica lab deployment backed by a mounted volume

## Logging

The app writes structured JSON logs to stdout. This keeps it compatible with the monitoring labs and makes request lifecycle events easy to inspect in Docker or Kubernetes.
