# DevOps Info Service (Python / FastAPI)

## Overview

This project implements a **DevOps Info Service** – a small web API that reports information about the service, the system it runs on, runtime uptime, and the current request.  
The service is used in the DevOps Core Course as a base for further labs: containerization, CI/CD, monitoring, and Kubernetes deployment.

Main endpoints:
- `GET /` – detailed service, system, runtime and request information, plus a list of available endpoints.
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

### `GET /health` – Health check

Returns a minimal JSON body for liveness/readiness checks:

- `status` – always `"healthy"` when the service is running
- `timestamp` – current UTC time in ISO 8601 format
- `uptime_seconds` – service uptime in seconds

Example:

```bash
curl -s http://127.0.0.1:5000/health | jq
```

## Configuration

The application is configured via environment variables, with sensible defaults:

| Variable | Default    | Description                                       |
|----------|------------|---------------------------------------------------|
| `HOST`   | `0.0.0.0`  | Interface to bind the server to                  |
| `PORT`   | `5000`     | TCP port to listen on                            |
| `DEBUG`  | `false`    | When `true`, enables auto-reload for development |

These values are read in `app.py` using `os.getenv(...)` and passed to `uvicorn.run()` when the app is started with `python app.py`.

## Development Notes

- The service is implemented with **FastAPI** and served by **uvicorn**.
- Runtime uptime is calculated from the application start time using `datetime` and `timezone.utc`.
- System information is collected via the standard `platform` and `socket` modules.

