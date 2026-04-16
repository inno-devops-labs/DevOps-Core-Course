# DevOps Info Service (Python / FastAPI)

[![Python CI](https://github.com/Vlad1mirZhidkov/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)](https://github.com/Vlad1mirZhidkov/DevOps-Core-Course/actions/workflows/python-ci.yml)
[![Coverage](https://codecov.io/gh/Vlad1mirZhidkov/DevOps-Core-Course/graph/badge.svg)](https://codecov.io/gh/Vlad1mirZhidkov/DevOps-Core-Course)

## Overview

DevOps Info Service is a small web API that reports:
- Service metadata
- System information
- Runtime health and uptime
- Basic request details

It is designed as a foundation for later labs (Docker, CI/CD, monitoring, and Kubernetes).

## Prerequisites

- Python 3.11 or newer
- `pip` (usually bundled with Python)

## Installation

Create a virtual environment and install dependencies:

```bash
python -m venv venv
```

Activate it:

```bash
# Linux / macOS
source venv/bin/activate

# Windows PowerShell
venv\Scripts\Activate.ps1
```

Install requirements:

```bash
pip install -r requirements.txt
```

## Running the Application

You can run via `python app.py` (it starts Uvicorn internally):

```bash
python app.py
```

Or run Uvicorn directly:

```bash
# From the app_python directory
uvicorn app:app --host 0.0.0.0 --port 5000

# From the repository root
uvicorn app_python.app:app --host 0.0.0.0 --port 5000
```

Run with custom configuration:

```bash
# Bash-style
PORT=8080 python app.py

# Windows PowerShell
$env:PORT=8080
python app.py
```

Try the endpoints:

```bash
curl http://127.0.0.1:5000/
curl http://127.0.0.1:5000/health
```

## Testing

Install dev dependencies:

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

Run tests:

```bash
# From the repository root
pytest app_python/tests

# From the app_python directory
pytest tests
```

Optional coverage report:

```bash
pytest app_python/tests --cov=app_python --cov-report=term-missing --cov-report=xml --cov-fail-under=70
```

## Docker

Build the image locally (run from `app_python`):

```bash
docker build -t <image>:<tag> .
```

Run a container with port mapping:

```bash
docker run --rm -p <host_port>:5000 -e PORT=5000 <image>:<tag>
```

Pull from Docker Hub:

```bash
docker pull <dockerhub-username>/<image>:<tag>
```

## API Endpoints

- `GET /` - Service and system information (increments visit counter)
- `GET /health` - Health check for probes and monitoring
- `GET /visits` - Returns the total number of visits to the root endpoint

## Persistent Visits Counter

The application tracks how many times the root endpoint (`/`) has been called.
The counter is stored in a plain text file at the path set by the `VISITS_FILE`
environment variable (default: `/data/visits`).

On each request to `/`:
1. The counter file is read (defaults to `0` if missing).
2. The value is incremented and written back atomically (cross-platform file locking:
   `fcntl` on Unix-like systems and `msvcrt` on Windows).
3. The new count is included in the JSON response under the `visits` key.

The `/visits` endpoint lets you query the current count without modifying it.

### Docker Compose (with persistence)

```bash
# From app_python/
docker compose up --build
curl http://localhost:5000/
curl http://localhost:5000/visits
# Linux / macOS
cat ./data/visits

# Windows PowerShell
Get-Content .\data\visits

# Restart and verify counter continues from where it left off
docker compose restart
curl http://localhost:5000/visits
```

The bind mount `./data:/data` keeps the counter file on the host filesystem, so
the value survives container restarts and recreations.

## Configuration

The service is configured through environment variables:

| Variable | Default | Description |
| --- | --- | --- |
| `HOST` | `0.0.0.0` | Host interface to bind |
| `PORT` | `5000` | Port to listen on |
| `DEBUG` | `false` | Enable debug-level logging |
| `VISITS_FILE` | `/data/visits` | Path to the visit counter file |
