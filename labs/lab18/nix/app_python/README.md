![CI](https://github.com/sayfetik/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)

[![Coverage Status](https://coveralls.io/repos/github/sayfetik/DevOps-Core-Course/badge.svg?branch=lab03)](https://coveralls.io/github/sayfetik/DevOps-Core-Course?branch=lab03)

# DevOps Info Service

## Overview
A simple Python web service that provides system and runtime information.

## Prerequisites
- Python 3.11+
- Flask==3.1.0

## Installation
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Running the Application
```bash
python app.py
# Or with custom config
PORT=8080 python app.py
```

## API Endpoints
- **GET /** - Service and system information
- **GET /health** - Health check

## Docker

This application can be run inside a Docker container.

### Build Docker Image

Use Docker to build the image locally from the Dockerfile:

```bash
docker build -t info-service .
```

### Run Docker Container

Run the container and expose the application port to the host:

```bash
docker run -p <host_port>:<container_port> info-service
```

You can also configure the service using environment variables:

```bash
docker run -e PORT=<port> -p <host_port>:<port> info-service
```

### Pull Image from Docker Hub

If the image is published to Docker Hub, it can be pulled directly:

```bash
docker pull <dockerhub_username>/info-service
```

### Persistence Features

The application now tracks visit counts persistently:

- **Endpoint**: `/visits` returns current visit count
- **Storage**: Count stored in `/data/visits.txt`
- **File locking**: Uses `fcntl` for concurrent access safety
- **Persistence**: Data survives container restarts via Docker volumes

### Testing Persistence

```bash
# Make requests
curl http://localhost:5050/
curl http://localhost:5050/visits

# Restart container
docker-compose restart

# Verify count persisted
curl http://localhost:5050/visits
```
