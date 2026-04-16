# DevOps Info Service

A Python web service that reports system information and health status through a simple REST API.

[![Python CI](https://github.com/hikariatama/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg?branch=lab3)](https://github.com/hikariatama/DevOps-Core-Course/actions/workflows/python-ci.yml)
[![Coverage](https://codecov.io/gh/hikariatama/DevOps-Core-Course/branch/lab3/graph/badge.svg?flag=app_python)](https://codecov.io/gh/hikariatama/DevOps-Core-Course)

## Prerequisites

- Python 3.11+
- pip

## Installation

```bash
cd app_python
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

## Running

```bash
python app.py
```

With custom configuration:

```bash
PORT=8080 python app.py
HOST=127.0.0.1 PORT=3000 python app.py
DEBUG=true python app.py
```

For production, use gunicorn:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Configuration and persistence

The service reads two external files when they are available:

- `APP_CONFIG_PATH` points to a JSON config file. Default: `/config/config.json`
- `VISITS_FILE_PATH` points to the visits counter file. Default: `/data/visits`

If the config file is missing, the app falls back to built-in defaults. If the visits file is missing, the app creates it and starts from `0`.

The root endpoint increments the counter and stores it in the visits file. The `/visits` endpoint returns the current value without incrementing it.

Example:

```bash
APP_CONFIG_PATH=./config/config.json VISITS_FILE_PATH=./data/visits python app.py
```

## Testing

Run linting:

```bash
python -m ruff check app.py tests
```

Run unit tests:

```bash
python -m pytest
```

Run unit tests with coverage and threshold:

```bash
python -m pytest --cov=app --cov-report=term-missing --cov-report=xml --cov-fail-under=70
```

## Docker

Build image locally:

```bash
docker build -t devops-info-service-python:lab12 .
```

Run container:

```bash
docker run --rm -p 5000:5000 \
  -e APP_CONFIG_PATH=/config/config.json \
  -e VISITS_FILE_PATH=/data/visits \
  -v "$(pwd)/config:/config:ro" \
  -v "$(pwd)/data:/data" \
  devops-info-service-python:lab12
```

Run with Docker Compose:

```bash
mkdir -p data
docker compose up --build
curl http://127.0.0.1:5000/ | python -m json.tool
curl http://127.0.0.1:5000/visits | python -m json.tool
```

## API Endpoints

### GET /

Returns service info, system details, runtime stats, effective configuration, and the updated visits count.

```bash
curl http://localhost:5000/ | python -m json.tool
```

### GET /visits

Returns the current visits counter without changing it.

```bash
curl http://localhost:5000/visits | python -m json.tool
```

### GET /health

Health check for monitoring and container orchestration.

```bash
curl http://localhost:5000/health
```

## Configuration

| Variable | Default | Description |
| -------- | ------- | ----------- |
| `HOST` | `0.0.0.0` | Host address |
| `PORT` | `5000` | Port number |
| `DEBUG` | `false` | Debug mode |
| `APP_CONFIG_PATH` | `/config/config.json` | JSON config file path |
| `VISITS_FILE_PATH` | `/data/visits` | Visits counter file path |
| `APP_ENV` | `dev` | Effective environment value |
| `APP_LOG_LEVEL` | `INFO` | Log level override |

Settings such as the greeting and feature flags come from `config.json`, which makes them reloadable when the mounted file changes.

## Troubleshooting

**Port in use:** Use a different port with `PORT=8080 python app.py`

**Import errors:** Make sure venv is activated and dependencies are installed

**Permission denied:** Use port > 1024 or run with elevated privileges

**Visits file not updating:** Make sure the directory behind `VISITS_FILE_PATH` is mounted and writable
