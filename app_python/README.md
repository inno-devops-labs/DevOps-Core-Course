# DevOps Info Service
[![Python CI](https://github.com/saddogsec/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)](...)
## Overview
This service reports:
- Service metadata (name, version, framework)
- System data (hostname, operating system, cpu, python version)
- Runtime data (uptime and current UTC time)
- Request metadata (IP, user agent, method, path)
- Visit counter (persists to file, survives restarts)

## Prerequisites
- Python 3.11+

## Installation
```bash
cd app_python
python -m venv venv
source venv/bin/activate # or source `venv/bin/activate.fish` if you using fish instead of bash/sh.
pip install -r requirements.txt
```

## Running the Application
```bash
python app.py

# Or with custom config
PORT=8080 python app.py
```

## API Endpoints
- `GET /` - Service and system information (increments visit counter)
- `GET /health` - Health check
- `GET /ready` - Readiness check
- `GET /visits` - Current visit count

## Configuration
- `HOST` - Interface to bind (0.0.0.0 by default)
- `PORT` - Port to listen on (5000 by default)
- `DEBUG` - Enable Flask debug logging (False by default)
- `DATA_DIR` - Directory for persistent data file (/data by default)

## Docker
- **Build image:**
```
docker build -t <image-name> .
```
- **Get image from dockerhub:**
```
docker pull saddogsec/devops-info-service:1.0.0
```
- **Run the image**
```
docker run -p 5000:5000 saddogsec/devops-info-service:1.0.0
```

## Docker Compose
The application can be run with Docker Compose, which mounts a volume for persistent visit counts:
```bash
docker compose up -d
```
This mounts `./data` to `/data` inside the container, so visit counts persist across restarts.
