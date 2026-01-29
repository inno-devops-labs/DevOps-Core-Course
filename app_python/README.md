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

## Docker

> Note: Commands below are shown as **examples** using the Docker Hub repository
> `egrapa/devops-core-course-lab2`. Replace the tag if you use a different one.

### Build (local) — example
```bash
docker build -t egrapa/devops-core-course-lab2:lab02 app_python/
```

### Run — example
```bash
docker run --rm -p 8080:5000 --name devops-info egrapa/devops-core-course-lab2:lab02
```

Test from host:
```bash
curl -s http://127.0.0.1:8080/health | python -m json.tool
curl -s http://127.0.0.1:8080/ | python -m json.tool
```

### Push to Docker Hub — example
```bash
docker login
docker push egrapa/devops-core-course-lab2:lab02
```

### Pull from Docker Hub — example
```bash
docker pull egrapa/devops-core-course-lab2:lab02
docker run --rm -p 8080:5000 egrapa/devops-core-course-lab2:lab02
```

## Notes
- All timestamps are returned in **UTC**
- Uptime is calculated since process start
- Client IP is resolved via `X-Forwarded-For` (if present) or `remote_addr`
- Error responses (404 / 500) are returned in JSON format

## Development Notes
- Code follows PEP 8 style guidelines
- Dependencies are pinned for reproducibility
- Logging is implemented using Python's standard `logging` module
