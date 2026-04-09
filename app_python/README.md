[![Python CI](https://github.com/SerggAidd/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)](https://github.com/SerggAidd/DevOps-Core-Course/actions/workflows/python-ci.yml)
# DevOps Info Service (Lab 01)

Small Flask web app for DevOps labs.

Provides:
- `GET /` — service/system/runtime/request info + list of endpoints
- `GET /health` — simple health check endpoint (for monitoring / K8s probes)

Configuration is done via environment variables: `HOST`, `PORT`, `DEBUG`.

---

## Overview

This service returns diagnostic information about:
- service metadata (name/version/description/framework)
- host system (hostname/platform/arch/CPU/python)
- runtime (uptime + current UTC time)
- current request (client IP, user-agent, method, path)
- available API endpoints (generated from Flask URL map)

---

## Prerequisites

- Python **3.11+** (Flask 3.x)
- pip / venv

---

## Installation

```bash
cd app_python

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

---

## Running the Application

Default (0.0.0.0:5000):
```bash
python app.py
```

Custom port:
```bash
PORT=8080 python app.py
```

Custom host + port:
```bash
HOST=127.0.0.1 PORT=3000 python app.py
```

Enable debug-level logging (and Flask debug mode):
```bash
DEBUG=true python app.py
```

---

## API Endpoints

### `GET /`

Returns full service + runtime info.

Example:
```bash
curl -s http://127.0.0.1:5000/ | jq '{service, system, runtime, request, endpoints}'
```

Response structure:
```json
{
  "service": {
    "description": "DevOps course info service",
    "framework": "Flask",
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "system": {
    "architecture": "x86_64",
    "cpu_count": 24,
    "hostname": "SerggAidd",
    "platform": "Linux",
    "platform_version": "6.18.5-arch1-1",
    "python_version": "3.14.2"
  },
  "runtime": {
    "current_time": "2026-01-23T18:16:16Z",
    "timezone": "UTC",
    "uptime_human": "0 hour, 0 minutes",
    "uptime_seconds": 4
  },
  "request": {
    "client_ip": "127.0.0.1",
    "method": "GET",
    "path": "/",
    "user_agent": "curl/8.18.0"
  },
  "endpoints": [
    {
      "description": "Root endpoint: returns service metadata and diagnostic information.",
      "method": "GET",
      "path": "/"
    },
    {
      "description": "Health check endpoint for monitoring and Kubernetes probes.",
      "method": "GET",
      "path": "/health"
    }
  ]
}
```

> Note: JSON object key ordering is not guaranteed by the HTTP/JSON standard.
> Use `python -m json.tool` or `jq` (like in example) only for pretty printing.

### `GET /health`

Health endpoint for monitoring / Kubernetes probes.

Example:
```bash
curl -s http://127.0.0.1:5000/health | python -m json.tool
```

Response:
```json
{
    "status": "healthy",
    "timestamp": "2026-01-23T21:25:39Z",
    "uptime_seconds": 43
}
```

Always returns HTTP **200** when service is running.

---

## Error Handling

- Unknown routes return JSON 404:

Example:
```bash
curl -i http://127.0.0.1:5000/does-not-exist
```

Response:
```json
{"error":"Not Found","message":"Endpoint does not exist"}
```

- Internal errors return JSON 500 (test endpoint is intentionally NOT included by default).

Example:
```bash
curl -i http://127.0.0.1:5000/crash
```
Response:
```json
{"error":"Internal Server Error","message":"An unexpected error occurred"}
```

---

## Logging

The app logs to **stdout**, which is the recommended approach for Docker/Kubernetes.

Logged events:
- request metadata before handling (`@app.before_request`)
- response status code after handling (`@app.after_request`)
- custom 404/500 handlers

---

## Configuration

| Variable | Default   | Description |
|---------:|-----------|-------------|
| `HOST`   | `0.0.0.0` | Bind address |
| `PORT`   | `5000`    | Listen port |
| `DEBUG`  | `False`   | `true` enables Flask debug mode and DEBUG logging |

---
## Docker
Below are the basic commands for building and running an application in a container.

### Local image build
```bash
cd app_python
docker build -t app_python:1.0 .
```

### Starting a container
The container listens on port 5000 internally, so we forward it to the host port (in the case bellow 8080)
```bash
docker run --rm -p 8080:5000 app_python:1.0
```
Example of running with variables:
```bash
docker run --rm -p 8080:5000 -e PORT=5000 -e DEBUG=false app_python:1.0
```
After that you can check endpoints in browser or in defferent terminal:
```bash 
curl http://localhost:8080/
curl http://localhost:8080/health
```

### Docker Hub (pull/run)
The image of this container publlished in Docker Hub. Image can be download with the following method:
```bash
docker pull sergey173/app_python:1.0.0
docker run --rm -p 8080:5000 sergey173/app_python:1.0.0
```

### Local Testing:
1. Install dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```
2. Lint:
```bash
flake8 app.py tests
```
3. Unit tests:
```bash
pytest -q
```

### Docker Compose persistence test (Lab 12 Task 1)
Use Docker Compose to verify that the visits counter survives container restarts.

```bash
cd app_python
docker compose up -d --build
curl http://localhost:5000/
curl http://localhost:5000/visits
docker compose restart
curl http://localhost:5000/visits
```

Expected result:
- each request to `GET /` increments the counter;
- `GET /visits` returns the current value;
- after `docker compose restart`, the counter value is preserved;
- the value is stored in the host-mounted file `./data/visits`.

### Local Testing:
1. Install dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```
2. Lint:
```bash
flake8 app.py tests
```
3. Unit tests:
```bash
pytest -q