![CI](https://github.com/ostxxp/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)

# DevOps Info Service (Labs 01–03)

## Overview
Simple web service that returns service, system, runtime and request information.

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
PORT=8080 python app.py
HOST=127.0.0.1 PORT=3000 python app.py
```

## API Endpoints

- `GET /` - Service and system information
- `GET /health` - Health check
## Configuration

|Variable|Default|Description|
|---|---|---|
|HOST|0.0.0.0|Bind host|
|PORT|5000|Bind port|
|DEBUG|False|Flask debug mode

## Docker

This app can be containerized and run with Docker.

**Build (pattern):**

- `docker build -t <image-name>:<tag> -f app_python/Dockerfile app_python`

**Run (pattern):**

- `docker run --rm -p <host-port>:5000 <image-name>:<tag>`
- Optional envs: `-e PORT=5000 -e HOST=0.0.0.0`

**Test endpoints (pattern):**

- `curl http://localhost:<host-port>/`
- `curl http://localhost:<host-port>/health`

**Pull from Docker Hub (pattern):**

- `docker pull <dockerhub-username>/<repo>:<tag>`
- then run it with the same `docker run -p ...` pattern

Example:
`docker run --rm -p 5000:5000 ostxxp/devops-lab02-python:latest`

