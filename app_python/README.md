# DevOps Course Info Service

## CI/CD status & coverage

![Python CI/CD Pipeline](https://github.com/setterwars/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)
[![codecov](https://codecov.io/gh/setterwars/DevOps-Core-Course/branch/master/graph/badge.svg)](https://codecov.io/gh/setterwars/DevOps-Core-Course)


## Overview

DevOps Info Service - small Flask based service what return and report system metadata and information.

## Prerequisites
- Python 3.11+
- pip 
-  Linux / macOS / Windows

## Installation guid

1. Clone the repository:
   ```bash
   git clone git@github.com:setterwars/DevOps-Core-Course.git
   
2. Navigate to the project directory:
   ```bash
   cd app_python

3. (Optional) Create and activate a virtual environment:
   ```bash
    python3 -m venv venv

4. Install the required dependencies:
   ```bash
   pip install -r requirements.txt

5. Run the application:
    ```bash
    python3 app.py # in default mode
    PORT=8080 HOST=127.0.0.1 DEBUG=True python3 app.py # in custom mode

## Available Endpoints
- `GET /` - Returns system metadata including hostname, IP address, and current timestamp.
- `GET /health` - Returns the health status of the service.
- `GET /visits` - Returns the persistent visits counter stored on disk.
- `GET /metrics` - Returns Prometheus metrics in text exposition format.


## Docker 

### Build the image locally (pattern)
```bash
docker build -t ${DOCKER_USER}devops-info-service-python:latest
```

### Run a container (pattern)
```bash
docker run --rm \
   -p 5000:5000 \
   -e HOST=0.0.0.0 \
   -e PORT=5000 \
   -e DEBUG=True \
   -e APP_CONFIG_PATH=/config/config.json \
   -e VISITS_FILE=/data/visits \
   -v "$(pwd)/data:/data" \
   -v "$(pwd)/config:/config:ro" \
   ${DOCKER_USER}/devops-info-service-python:latest
```

### Local persistence test with Docker Compose
```bash
mkdir -p data
docker compose up --build -d
curl http://127.0.0.1:5000/
curl http://127.0.0.1:5000/
curl http://127.0.0.1:5000/visits
cat data/visits
docker compose restart app
curl http://127.0.0.1:5000/visits
docker compose down
```

The compose file mounts `./data` to `/data` so the visits counter survives container restarts, and mounts `./config/config.json` into `/config/config.json` for externalized configuration.

### Pull from Docker Hub
Link to docker hub: 

https://hub.docker.com/repository/docker/zsalavat/devops-info-service-python/general

```bash
docker pull zsalavat/devops-info-service-python
docker run --rm -p 5000:5000 zsalavat/devops-info-service-python:latest
```

### Test Running 

For running tests used `pytest`

for run test use:

```bash
pytest
```
