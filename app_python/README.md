# DevOps Info Service (Python)

## Overview
A simple DevOps info service that exposes system/runtime details, a health endpoint, and a persistent visit counter.

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

### How to run tests locally:
```bash
pip install -r app_python/requirements.txt
pip install -r app_python/requirements-dev.txt
pytest -v
```

## Docker

### Build locally
```bash
docker build -t python-app .
```

### Run container
```bash
docker run --rm -p 8000:8000 python-app
```

### Run with persistent visit storage
```bash
docker compose up --build
```

The Compose setup mounts `./data` into the container at `/data`, so the visit counter survives container restarts.

### Verify visit persistence
```bash
curl http://localhost:8000/
curl http://localhost:8000/
curl http://localhost:8000/visits
cat ./data/visits
docker compose down
docker compose up -d
curl http://localhost:8000/visits
```

`VISITS_FILE` defaults to `/data/visits`, but you can override it with an environment variable for local testing.

### Pull from Docker Hub
```bash
docker pull s1mphonia/devops-core-course-python-app:latest
docker run --rm -p 8000:8000 s1mphonia/devops-core-course-python-app
```
