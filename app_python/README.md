![Python CI badge](https://github.com/ilyalinhnguyen/DevOps-Core-Course/actions/workflows/lint-and-docker.yaml/badge.svg)

# DevOps Info Service (Python)

Python web application that exposes system info and a health check endpoint.

## Overview
This service reports:
- Service metadata (name/version/framework)
- System data (hostname, OS, CPU, Python version)
- Runtime data (uptime and current UTC time)
- Request metadata (client IP, user agent, method, path)

## Prerequisites
- Python 3.11+ recommended

## Installation
```bash
cd app_python
python -m venv venv
source venv/bin/activate # or source `venv/bin/activate.fish` if you using fish instead of bash/sh.
pip install -r requirements.txt
```

## Running the Application
```bash
python app.py

# Or with custom config
PORT=8080 python app.py
HOST=127.0.0.1 PORT=3000 python app.py
DEBUG=True python app.py
```

## API Endpoints
- `GET /` - Service and system information
- `GET /visits` - Current persisted visits count
- `GET /health` - Health check

## Configuration
| Env Var | Default | Description |
|---------|---------|-------------|
| `HOST`  | `0.0.0.0` | Interface to bind |
| `PORT`  | `5000` | Port to listen on |
| `DEBUG` | `False` | Enable Flask debug logging |
| `VISITS_FILE` | `/data/visits` | File path used for persisted visits counter |

## Example Requests
```bash
curl -s http://localhost:5000/ | jq .
curl -s http://localhost:5000/visits | jq .
curl -s http://localhost:5000/health | jq .
```

## Testing & Linting

Run locally from inside `app_python/`:

```bash
# unit tests (with coverage)
pytest

# lint + format checks
ruff check .
ruff format --check .
```

## Docker

### Build Image

Use the following pattern inside `app_python`:

- **Build image**:
  ```bash
  docker build -t python-app .
  ```

### Run Container

- **Run container with port mapping**:
  ```bash
  docker run --rm -p 5000:5000 python-app
  ```

- **Run with persistent visits file mounted from host**:
  ```bash
  docker run --rm -p 5000:5000 -v "$(pwd)/data:/data" python-app
  ```

- **Override host/port via environment variables (optional)**:
  ```bash
  docker run --rm -p 8080:8080 -e PORT=8080 -e HOST=0.0.0.0 python-app
  ```

### Docker Compose Persistence Test

From `app_python/`:

```bash
docker compose up -d
curl -s http://localhost:5001/ > /dev/null
curl -s http://localhost:5001/ > /dev/null
curl -s http://localhost:5001/visits | jq .
docker compose restart
curl -s http://localhost:5001/visits | jq .
docker compose down
```

### Pull from Docker Hub

- **Pull image**:
  ```bash
  docker pull pickpusha/devops-info-service-python:lab2
  ```

- **Run pulled image**:
  ```bash
  docker run --rm -p 5000:5000 pickpusha/devops-info-service-python:lab2
  ```
