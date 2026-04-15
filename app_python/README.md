# DevOps Info Service (Python / FastAPI)

![CI/CD Pipeline](https://github.com/McLavrushka/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)
![Codecov](https://codecov.io/gh/McLavrushka/DevOps-Core-Course/branch/lab03/graph/badge.svg)

## Overview

This project implements a **DevOps Info Service** – a small web API that reports information about the service, the system it runs on, runtime uptime, and the current request.  
The service is used in the DevOps Core Course as a base for further labs: containerization, CI/CD, monitoring, and Kubernetes deployment.

Main endpoints:
- `GET /` – detailed service, system, runtime and request information, plus a list of available endpoints. **(Lab 12)** Increments a persisted visit counter and returns `visits` in the JSON payload.
- `GET /visits` – **(Lab 12)** returns the current visit counter from disk (`VISITS_FILE`, default `/data/visits`).
- `GET /health` – lightweight health check with status, timestamp, and uptime in seconds.

## Prerequisites

- Python **3.11+** (tested with Python 3.14)
- `pip` for installing dependencies
- (Optional) Unix-like shell for the examples below

## Installation

From the project root:

```bash
cd app_python
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the Application

### Default configuration

```bash
cd app_python
source venv/bin/activate
python app.py
```

By default the service runs on:

- Host: `0.0.0.0`
- Port: `5000`

Open in your browser:

- `http://127.0.0.1:5000/`
- `http://127.0.0.1:5000/health`
- `http://127.0.0.1:5000/docs` – auto-generated Swagger UI

### Custom configuration via environment variables

```bash
# Custom port
PORT=8080 python app.py

# Custom host and port
HOST=127.0.0.1 PORT=3000 python app.py

# Enable debug reload mode
DEBUG=true python app.py
```

## API Endpoints

### `GET /` – Service and system information

Returns a JSON object with the following structure:

- `service`:
  - `name` – service name (`devops-info-service`)
  - `version` – application version (`1.0.0`)
  - `description` – short description
  - `framework` – web framework used (`FastAPI`)
- `system`:
  - `hostname` – machine hostname
  - `platform` – OS name (e.g. `Darwin`, `Linux`)
  - `platform_version` – detailed OS version
  - `architecture` – CPU architecture (e.g. `arm64`, `x86_64`)
  - `cpu_count` – CPU identifier / count
  - `python_version` – Python runtime version
- `runtime`:
  - `uptime_seconds` – service uptime in seconds since start
  - `uptime_human` – human-readable uptime string
  - `current_time` – current UTC time in ISO 8601 format
  - `timezone` – timezone used (`UTC`)
- `request`:
  - `client_ip` – client IP address
  - `user_agent` – HTTP User-Agent header
  - `method` – HTTP method (e.g. `GET`)
  - `path` – request path
- `endpoints` – list of available endpoints:
  - `path` – endpoint path
  - `method` – HTTP method
  - `description` – short description

Example:

```bash
curl -s http://127.0.0.1:5000/ | jq
```

### `GET /visits` – Visit counter (Lab 12)

Returns JSON:

- `visits` – integer count persisted in `VISITS_FILE` (default `/data/visits`)
- `file` – path to the counter file

Does **not** increment the counter (use `GET /` for that).

### `GET /health` – Health check

Returns a minimal JSON body for liveness/readiness checks:

- `status` – always `"healthy"` when the service is running
- `timestamp` – current UTC time in ISO 8601 format
- `uptime_seconds` – service uptime in seconds

Example:

```bash
curl -s http://127.0.0.1:5000/health | jq
```

## Testing

The project includes comprehensive unit tests using `pytest`. All tests are located in the `tests/` directory.

### Running Tests Locally

From the `app_python` directory:

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Install dependencies (includes pytest)
pip install -r requirements.txt

# 3. Run all tests
pytest tests/ -v

# 4. Run tests with coverage report
pytest tests/ --cov=app --cov-report=term

# 5. Run specific test file
pytest tests/test_root.py -v
pytest tests/test_health.py -v
```

### Test Structure

Tests are organized into separate files:
- `test_root.py` - Tests for `GET /` endpoint (8 tests)
- `test_health.py` - Tests for `GET /health` endpoint (5 tests)
- `test_errors.py` - Tests for error handling (404 responses) (3 tests)
- `test_consistency.py` - Tests for consistency between endpoints (2 tests)

**Total:** 17 tests covering all endpoints and error cases.

**Test Coverage:** 88% (as measured by `pytest-cov`)

## Configuration

The application is configured via environment variables, with sensible defaults:

| Variable | Default    | Description                                       |
|----------|------------|---------------------------------------------------|
| `HOST`   | `0.0.0.0`  | Interface to bind the server to                  |
| `PORT`   | `5000`     | TCP port to listen on                            |
| `DEBUG`  | `false`    | When `true`, enables auto-reload for development |
| `VISITS_FILE` | `/data/visits` | **(Lab 12)** Path to the visit counter file |
| `CONFIG_JSON_PATH` | `/config/config.json` | **(Lab 12)** Optional JSON config from a ConfigMap mount |

These values are read in `app.py` using `os.getenv(...)` and passed to `uvicorn.run()` when the app is started with `python app.py`.

## Lab 12 — Docker Compose (visit persistence)

From `app_python/`:

```bash
docker compose up --build
```

- Host directory `./data` is mounted to `/data` in the container.
- Hit `http://127.0.0.1:5000/` several times, then `http://127.0.0.1:5000/visits`.
- Run `docker compose restart` and confirm `/visits` continues from the last value.
- Inspect `app_python/data/visits` on the host if needed.

For Kubernetes / Helm, see `k8s/CONFIGMAPS.md`.

## Docker

The application can be containerized using Docker for consistent deployment across environments.

### Building the Image

Build the Docker image from the `app_python` directory:

```bash
docker build -t <image-name>:<tag> .
```

Example:
```bash
docker build -t devops-info-service:latest .
```

### Running a Container

Run a container from the built image with port mapping:

```bash
docker run -d -p <host-port>:5000 --name <container-name> <image-name>:<tag>
```

Example:
```bash
docker run -d -p 5000:5000 --name devops-service devops-info-service:latest
```

The application will be accessible at `http://localhost:<host-port>/` and `http://localhost:<host-port>/health`.

### Custom Configuration

You can override environment variables when running the container:

```bash
docker run -d -p 8080:5000 -e PORT=5000 -e DEBUG=false <image-name>:<tag>
```

### Pulling from Docker Hub

If the image is published to Docker Hub, you can pull and run it:

```bash
docker pull <docker-hub-username>/<image-name>:<tag>
docker run -d -p 5000:5000 <docker-hub-username>/<image-name>:<tag>
```


## Development Notes

- The service is implemented with **FastAPI** and served by **uvicorn**.
- Runtime uptime is calculated from the application start time using `datetime` and `timezone.utc`.
- System information is collected via the standard `platform` and `socket` modules.

