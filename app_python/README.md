# DevOps Info Service (Python)

![Python CI and Docker](https://github.com/chomosuce/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)
[![Ansible Deployment](https://github.com/chomosuce/DevOps-Core-Course/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/chomosuce/DevOps-Core-Course/actions/workflows/ansible-deploy.yml)

## Overview
Simple Flask web service that reports service metadata, system details, runtime uptime, and request info. Includes `/health` for liveness probes and a persistent visits counter available on `/visits`.

## Prerequisites
- Python 3.11+
- pip

## Installation
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Testing
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
pytest
```

## Running the Application
```bash
python app.py
# Custom configuration
PORT=8080 python app.py
HOST=127.0.0.1 PORT=3000 DEBUG=true python app.py
```

## API Endpoints
- `GET /` — Service, system, runtime, request info, and endpoint list.
- `GET /visits` — Current total visits count persisted to file.
- `GET /health` — Health status and uptime (HTTP 200).

## Configuration
Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST`   | `0.0.0.0` | Bind address |
| `PORT`   | `8080`  | Listening port |
| `DEBUG`  | `False` | Enable Flask debug mode |
| `VISITS_FILE` | `data/visits` | File path used for persisted visits counter |

## Notes
- Logging is configured at startup; noisy werkzeug logs are suppressed to WARNING.
- Error handlers return JSON for 404 and 500.

## Docker
- Build an image from this directory: `docker build -t devops:<tag> .`
- Run the container (maps port 8080 by default): `docker run -p 8080:8080 devops:<tag>`
- Pull from Docker Hub once published: `docker pull devops:<tag>`

## Local Persistence Check (Docker Compose)
Use the repository compose stack in `monitoring/docker-compose.yml` (the app service mounts `../app_python/data:/data`):

```bash
cd monitoring
docker compose up -d app-python
curl -s http://127.0.0.1:8000/
curl -s http://127.0.0.1:8000/visits
cat ../app_python/data/visits
docker compose restart app-python
curl -s http://127.0.0.1:8000/visits
```

The visits counter should continue from the same value after restart.
