# DevOps Info Service (Python)

## Overview
A small web service that reports service metadata, system info, runtime uptime, and request details.  
It provides two endpoints: `/` (full info) and `/health` (health check).

## Prerequisites
- Python **3.11+**
- pip

## Installation
```bash
cd app_python
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the Application
   ```bash
   python app.py
   ```
## API Endpoints
   - `GET /` - Service and system information
   - `GET /health` - Health check
   - `GET /visits` - Current persisted visits counter

## Configuration 
    ```bash
    HOST = "0.0.0.0"
    PORT = "5000"
    DEBUG = "False"
   VISITS_FILE = "/data/visits"
    ```

## Visits Counter Persistence

- Each request to `GET /` increments a counter.
- Counter value is stored in a file (`VISITS_FILE`, default `/data/visits`).
- `GET /visits` returns current value and file location.
- File updates use atomic replace to reduce race-condition risk.

## Docker

### Build
```bash
docker build -t <dockerhub-username>/devops-info-python:lab02 .
```

### Run
```bash
docker run --rm -p <host_port>:5000 <dockerhub-username>/devops-info-python:lab02
```

### Run with persistent volume (docker-compose)
```bash
docker compose up -d --build
curl http://localhost:5000/
curl http://localhost:5000/visits
cat ./data/visits
docker compose restart
curl http://localhost:5000/visits
```

### Pull from Docker Hub
```bash
docker pull <dockerhub-username>/devops-info-python:lab02
docker run --rm -p <host_port>:5000 <dockerhub-username>/devops-info-python:lab02
```

### Github status badge

[![python-ci](https://github.com/olesia8novoselova/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)](https://github.com/olesia8novoselova/DevOps-Core-Course/actions/workflows/python-ci.yml)