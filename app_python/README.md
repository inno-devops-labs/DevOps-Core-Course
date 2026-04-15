# DevOps Info Service

## Docker images

https://hub.docker.com/repository/docker/plaffyyy9/devops-info-service/image-management

## Quick Start

```bash
pip install -r requirements.txt
python app.py
```

## Testing

```
pytest tests/ -v --cov=app --cov-report=html
open htmlcov/index.html  # 94% coverage
```

## Overview

Lightweight web service providing system information, runtime status, and health checks. Foundation for comprehensive DevOps monitoring throughout the course.

## Prerequisites

* Python 3.11+
* pip
* git

## Installation

```
python3.11 -m venv venv
source venv/bin/activate      # Linux/Mac
pip install -r requirements.txt
```

## Running the Application

```
python app.py                    # Default: http://0.0.0.0:5000
PORT=8080 python app.py          # Custom port
HOST=127.0.0.1 PORT=3000 python app.py  # Specific host/port
DEBUG=true python app.py         # Debug mode (auto-reload)

```

## API Endpoints

| Endpoint    | Method | Description                          |
| ----------- | ------ | ------------------------------------ |
| `/`       | GET    | Service, system, runtime information |
| `/visits` | GET    | Current persisted visits counter     |
| `/health` | GET    | Health status for monitoring         |

```
curl http://localhost:5000/
curl http://localhost:5000/visits
curl http://localhost:5000/health
```

## Configuration

Environment variables for flexible deployment:

| Variable  | Default     | Description                   |
| --------- | ----------- | ----------------------------- |
| `HOST`  | `0.0.0.0` | Bind address                  |
| `PORT`  | `5000`    | TCP port                      |
| `DEBUG` | `False`   | Debug mode (development only) |
| `VISITS_FILE` | `/data/visits` | Path to persisted visits counter file |

**Example** :

```
export HOST=0.0.0.0
export PORT=8080
export DEBUG=true
python app.py

```

# Docker build

```bash
docker build -t plaffyyy9/devops-info-service:lab2 .
```

## Local run

```
docker run --rm -p 8081:5001 plaffyyy9/devops-info-service:lab2
```

Open http://localhost:8081/

## Pull from Docker Hub

```
docker pull plaffyyy9/devops-info-service:lab2
docker run --rm -p 8081:5001 plaffyyy9/devops-info-service:lab2
```

## Docker Compose with persisted visits counter

```bash
mkdir -p data
docker compose up -d --build

curl http://localhost:5001/
curl http://localhost:5001/
curl http://localhost:5001/visits
cat ./data/visits

docker compose restart devops-info-service
curl http://localhost:5001/visits
```

The value in `./data/visits` is preserved after container restart.
