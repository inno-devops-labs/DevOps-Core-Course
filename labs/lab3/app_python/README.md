# DevOps Info Service (Python / Flask)

A small web service that exposes basic system and runtime information via HTTP.  
This repository contains the **Python/Flask** implementation for the DevOps Core Course labs.

## Features
- `GET /` — JSON with service metadata, system info, runtime info, request info, and available endpoints
- `GET /health` — JSON health check with uptime
- Configurable via environment variables (`HOST`, `PORT`, `DEBUG`)
- JSON error handlers (404/500)
- Basic logging

## Local Run (venv)
### Prerequisites
- Python 3.12+
- `pip` / `venv`

### Install & Run
```bash
cd app_python

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python app.py
```

### Custom Host/Port
```bash
HOST=127.0.0.1 PORT=8080 python app.py
```

## Docker (Lab 2)
### Build
```bash
cd app_python
docker build -t devops-info-python:lab02 .
```

> Note: if you face DNS issues during image build, you can use:
```bash
docker build --network=host -t devops-info-python:lab02 .
```

### Run
```bash
docker run --rm -p 5000:5000 devops-info-python:lab02
```

### Test
```bash
curl -s http://localhost:5000/ | head
curl -s http://localhost:5000/health
```

## Docker Hub
Image was pushed to Docker Hub:
- Repository: `docker.io/akakii98/devops-info-python`
- Tag: `akakii98/devops-info-python:lab02`

Pull & run:
```bash
docker pull akakii98/devops-info-python:lab02
docker run --rm -p 5000:5000 akakii98/devops-info-python:lab02
```

## Status badge

[![Python CI](https://github.com/Rozanalex/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg?branch=master)](https://github.com/Rozanalex/DevOps-Core-Course/actions/workflows/python-ci.yml)


## Testing (local)
```bash
cd labs/lab3/app_python
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
ruff check .
pytest -q --cov=. --cov-report=term-missing --cov-report=xml
```

## Screenshots / Evidence
All screenshots are located here:
- `app_python/docs/screenshots/`

Lab 2 evidence:
- Build: `docs/screenshots/successful_docker_build.png`
- Run (container logs): `docs/screenshots/run_shell_custom_image.png`
- Curl tests (local image): `docs/screenshots/curl_to_custom_image.png`
- Push + Pull + Run (Docker Hub): `docs/screenshots/successful_pushing_custom_image.png`
- Curl tests (pulled image): `docs/screenshots/curl_to_pulled_custom_image.png`

## Notes
- `venv/` should not be committed (kept in `.gitignore` / `.dockerignore`).
