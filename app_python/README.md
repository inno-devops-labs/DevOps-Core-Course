# DevOps Info Service (Python / Flask)

## Overview
DevOps Info Service is a small HTTP web service that exposes information about
itself, the host system, runtime environment, and incoming HTTP requests.
It also provides a health-check endpoint intended for monitoring systems
and container orchestrators (Docker, Kubernetes).

This service serves as a foundation for future DevOps labs:
containerization, CI/CD pipelines, monitoring, and persistence.

## Prerequisites
- Python **3.11+**
- `pip`
- (recommended) virtual environment (`venv`)

## Installation
```bash
cd app_python
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the Application

### Default run
```bash
python app.py
```

The service will be available at:
```
http://0.0.0.0:5000
```

### Custom configuration
```bash
PORT=8080 python app.py
HOST=127.0.0.1 PORT=3000 python app.py
DEBUG=true python app.py
```

## API Endpoints

### `GET /`
Returns service metadata, system information, runtime details,
and request context.

Example:
```bash
curl -s http://127.0.0.1:5000/
```

Pretty-printed output:
```bash
curl -s http://127.0.0.1:5000/ | python -m json.tool
```

### `GET /health`
Health-check endpoint used for monitoring and readiness/liveness probes.

Example:
```bash
curl -s http://127.0.0.1:5000/health
```

Pretty-printed output:
```bash
curl -s http://127.0.0.1:5000/health | python -m json.tool
```

## Configuration

The application is configured via environment variables:

| Variable | Default | Description |
|--------|---------|-------------|
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `5000` | TCP port |
| `DEBUG` | `False` | Enables Flask debug mode and debug logging |

## Notes
- All timestamps are returned in **UTC**
- Uptime is calculated since process start
- Client IP is resolved via `X-Forwarded-For` (if present) or `remote_addr`
- Error responses (404 / 500) are returned in JSON format

## Development Notes
- Code follows PEP 8 style guidelines
- Dependencies are pinned for reproducibility
- Logging is implemented using Python's standard `logging` module