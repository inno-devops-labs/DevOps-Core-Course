# DevOps Info Service (FastAPI)

## Overview

[![python-ci](https://github.com/GrayMansion/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)](https://github.com/GrayMansion/DevOps-Core-Course/actions/workflows/python-ci.yml)

A small web service that exposes system/runtime information, metrics, and a persistent visits counter.

## Prerequisites
- Python 3.11+
- pip

## Installation
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the Application
```bash
python app.py
```

## Custom config:
```bash
PORT=8080 python app.py
HOST=127.0.0.1 PORT=3000 python app.py
DEBUG=true python app.py
```

## API Endpoints
```bash
GET / — Service and system information
GET /visits — Current visits counter value
GET /health — Health check
GET /metrics — Prometheus metrics
```

## Configuration
| Variable | Default | Meaning                                 |
| -------- | ------- | --------------------------------------- |
| HOST     | 0.0.0.0 | Bind address                            |
| PORT     | 5000    | Listening port                          |
| DEBUG    | False   | If true, enables reload + debug logging |
| VISITS_FILE | ./data/visits | File path for persistent visits counter |

## Docker

This project can be built and run as a Docker container (same API behavior as local run).

### Build the image
```bash
docker build -t <image_name>:<tag> -f app_python/Dockerfile app_python
```

### Run the container
The app listens on container port `<container_port>` (default is `5000`), so you publish it to a host port:

```bash
docker run --rm -p <host_port>:<container_port> <image_name>:<tag>
```

### Pull from Docker Hub
```bash
docker pull graymansion/devops-info-service:lab02
docker run --rm -p <host_port>:<container_port> graymansion/devops-info-service:lab02
```

## Local persistence test with Docker Compose

Run from app_python directory:

```bash
docker compose up --build -d
curl http://localhost:5000/
curl http://localhost:5000/
curl http://localhost:5000/visits
cat ./data/visits
docker compose restart
curl http://localhost:5000/visits
docker compose down
```

Expected result:
- Counter increments when / is called.
- The same counter value is kept after container restart because ./data is mounted to /app/data.

