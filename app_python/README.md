# DevOps Info Service

> Flask service that now covers the Lab 1 API, later monitoring work, and the Lab 12 persistence requirements.

## Overview

The service exposes four HTTP endpoints:
- `GET /` returns service metadata, system details, runtime info, runtime configuration, the current visits counter, and the published endpoint list. Every call increments the persistent visits counter.
- `GET /health` returns a lightweight health payload for probes and uptime checks.
- `GET /visits` returns the current persistent visits counter without incrementing it.
- `GET /metrics` returns Prometheus metrics used in later labs.

The visits counter is stored in a file so it survives container restarts when the file path is mounted to persistent storage. Runtime configuration can also be read from a JSON file, which makes the later ConfigMap mount visible through the API response.

## Prerequisites

- Python 3.11 or newer
- `pip`
- A virtual environment tool such as `venv`

## Installation

```bash
cd app_python
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

If your system uses `python` instead of `python3`, substitute that command accordingly.

## Running the Application

Run locally with the source-code defaults:

```bash
python app.py
```

This starts the service on `0.0.0.0:5000` and writes the visits counter to `./data/visits`.

Run with custom configuration:

```bash
HOST=127.0.0.1 PORT=3000 python app.py
DEBUG=true PORT=8080 python app.py
```

For a production-style local run:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Docker Compose Persistence Check

Lab 12 requires a local containerized persistence test. The repository now includes [`docker-compose.yml`](docker-compose.yml).

Start the service with a bind-mounted data directory:

```bash
cd app_python
docker compose up --build
```

The compose file binds the container's port `3000` to host port `3001` by default to avoid collisions with other local services. If `3000` is free on your machine, you can override it with `APP_HOST_PORT=3000 docker compose up --build`.

Then verify persistence:

```bash
curl http://127.0.0.1:3001/
curl http://127.0.0.1:3001/
curl http://127.0.0.1:3001/visits
cat ./data/visits
docker compose restart
curl http://127.0.0.1:3001/visits
```

The counter value in `./data/visits` should stay the same after the restart.

## API Endpoints

### `GET /`

Returns:
- `service`: service metadata
- `system`: hostname, platform, architecture, CPU count, Python version
- `runtime`: uptime, current UTC timestamp, timezone
- `request`: client IP, user agent, method, path
- `endpoints`: published endpoint list

Example request:

```bash
curl http://127.0.0.1:5000/
```

### `GET /health`

Returns service health status, current UTC timestamp, and uptime in seconds.

Example request:

```bash
curl http://127.0.0.1:5000/health
```

### `GET /visits`

Returns the current persistent visits counter and the file path used to store it.

Example request:

```bash
curl http://127.0.0.1:5000/visits
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `devops-info-service` | Service name reported by the API and logs |
| `APP_ENV` | `local` | High-level runtime environment name |
| `HOST` | `0.0.0.0` | Bind address for the Flask development server |
| `PORT` | `5000` | Listening port when running `python app.py` |
| `DEBUG` | `False` | Enables Flask debug mode |
| `LOG_LEVEL` | `INFO` | Root logging level for structured JSON logs |
| `VISITS_FILE_PATH` | `data/visits` | File used to persist the visits counter |
| `APP_CONFIG_PATH` | `config/config.json` | Optional JSON config file path used for runtime config inspection |

Note: the Docker image used in later labs sets `PORT=3000` explicitly, so containerized runs stay compatible with the rest of the course materials even though the Lab 1 source default is `5000`.

## Quality Checks

```bash
python -m ruff check .
python -m pytest tests/
```

Manual smoke checks:

```bash
curl http://127.0.0.1:5000/
curl http://127.0.0.1:5000/health
curl http://127.0.0.1:5000/visits
curl -i -X POST http://127.0.0.1:5000/
```

## Project Structure

```text
app_python/
├── app.py
├── config/
├── data/
├── docker-compose.yml
├── requirements.txt
├── .gitignore
├── README.md
├── tests/
│   ├── __init__.py
│   └── test_app.py
└── docs/
    ├── LAB01.md
    └── screenshots/
```
