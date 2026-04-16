![Python CI Pipeline](https://github.com/danielambda/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)
# DevOps Info Service


## Overview

The DevOps Info Service is a Python web application that provides runtime, system, and request information via a REST API.


## Features

* Exposes system and runtime information
* Health check endpoint for monitoring
* Persistent visits counter stored in a file
* Configurable via environment variables
* Clean, production-ready Flask application


## Tech Stack

* Python 3.11+
* Flask 3.1.0


## Prerequisites

Ensure the following are installed:

* Python 3.11 or newer
* pip package manager
* Optional: jq for formatted JSON output

Check Python version:

```bash
python --version
```


## Installation

Clone the repository and set up a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```


## Running the Application

Start the application with default settings:

```bash
python app.py
```

Access the service at:

```
http://localhost:5000
```

### Custom Configuration

Set environment variables to customize host, port, and debug mode:

```bash
HOST=127.0.0.1 PORT=8080 DEBUG=true python app.py
```


## API Endpoints

### GET /

Returns service metadata, system info, runtime details, request metadata, and available endpoints.

Example:

```bash
curl http://localhost:5000/
```

Pretty-printed output:

```bash
curl http://localhost:5000/ | jq
```

### GET /health

Health check endpoint for monitoring and readiness probes.

Example:

```bash
curl http://localhost:5000/health
```

Response:

```json
{
  "status": "healthy",
  "timestamp": "2026-01-07T14:30:00Z",
  "uptime_seconds": 3600
}
```

### GET /visits

Returns the current number of visits recorded by the root endpoint.

Example:

```bash
curl http://localhost:5000/visits
```

Response:

```json
{
  "visits": 5
}
```

## Configuration

| Environment Variable | Default | Description               |
| -------------------- | ------- | ------------------------- |
| HOST                 | 0.0.0.0 | Network interface to bind |
| PORT                 | 5000    | Application port          |
| DEBUG                | False   | Enable Flask debug mode   |
| VISITS_FILE          | /data/visits | File path for persisted visit counter |


## Docker

This application can also be run as a containerized service using Docker.
Containerization ensures consistent behavior across environments and removes the need to manage local Python dependencies.

### Build the Image Locally

Use the Dockerfile provided in this repository to build a local image:

```text
docker build -t <image-name> <path-to-app>
```

This creates a container image containing the application and its runtime dependencies.

---

### Run the Container

Run the container and map the container port to a host port:

```text
docker run -p <host-port>:<container-port> <image-name>
```

The application will be accessible via the mapped host port.

Environment variables such as `HOST`, `PORT`, and `DEBUG` can be passed at runtime using Docker options.

To persist visit counts across container restarts, mount a volume to `/data` (or set `VISITS_FILE` to a path inside a mounted volume).

---

### Pull from Docker Hub

If the image has already been published to Docker Hub, it can be pulled directly:

```text
docker pull <dockerhub-username>/<image-name>:<tag>
```

After pulling, the container can be started the same way as a locally built image.

---

### Notes

* The container runs as a **non-root user** for improved security.
* The containerized application behaves the same as when run locally.
* Docker ensures consistent execution across environments.


## Running Tests

Tests are written using pytest.

### Install dependencies
```bash
pip install -r requirements.txt -r requirements-dev.txt
```

### Run tests
```bash
pytest -v
```
