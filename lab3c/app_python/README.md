# DevOps Info Service (FastAPI)

[![Python CI](https://github.com/TsixPhoenix/DevOps-CC/actions/workflows/python-ci.yml/badge.svg?branch=lab03)](https://github.com/TsixPhoenix/DevOps-CC/actions/workflows/python-ci.yml)
[![Coverage](https://codecov.io/gh/TsixPhoenix/DevOps-CC/branch/lab03/graph/badge.svg)](https://codecov.io/gh/TsixPhoenix/DevOps-CC)

## Overview
Small service returning system info about the machine it runs on, plus a health check.

## Prerequisites
- Python 3.11+
- pip
- (Optional) venv tool

## Installation
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
```

## Running the Application
```bash
python app.py
```

Custom config examples:
```bash
PORT=8080 python app.py
HOST=127.0.0.1 PORT=3000 python app.py
```

FastAPI docs:
- `http://localhost:<port>/docs`

## Tests
Run locally:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=app --cov-report=term
```

## API Endpoints
- `GET /` - Service and system information
- `GET /health` - Health check

## Configuration
| Variable | Default | Description |
| --- | --- | --- |
| `HOST` | `0.0.0.0` | Bind address for the server |
| `PORT` | `5000` | Port to listen on |
| `DEBUG` | `False` | Enable auto-reload |

## Docker
Command patterns (replace the placeholders with your values):

**Build locally**
```bash
docker build -t <dockerhub-username>/<image-name>:<tag> .
```

**Run container**
```bash
docker run --rm -p <host-port>:5000 --name <container-name> <dockerhub-username>/<image-name>:<tag>
```

**Pull from Docker Hub**
```bash
docker pull <dockerhub-username>/<image-name>:<tag>
```

Optional env overrides:
```bash
docker run --rm -e PORT=5000 -e HOST=0.0.0.0 -p <host-port>:5000 <dockerhub-username>/<image-name>:<tag>
```
