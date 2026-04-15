# DevOps Info Service

A Flask web application used throughout the DevOps course labs.

## Overview

The service returns system and runtime information, exposes a health check, and now keeps a persistent visit counter backed by a file.

## Features

- `GET /` returns service metadata, host details, runtime info, request info, and the current visit count
- `GET /health` provides a lightweight health check for Kubernetes probes
- `GET /visits` returns the current visit counter without incrementing it
- Visit counts are stored in a file so they survive container restarts when a volume is mounted

## Requirements

- Python 3.10+
- `pip`

## Local Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the App

The application listens on `0.0.0.0:5000` by default.

```bash
python app.py
```

You can override the host, port, or visits file with environment variables:

```bash
HOST=127.0.0.1 PORT=8080 VISITS_FILE=/tmp/visits python app.py
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/` | Service information and increments the visit counter |
| GET | `/health` | Health check for Kubernetes |
| GET | `/visits` | Returns the current visit count |

Example response from `/visits`:

```json
{
  "visits": 4,
  "timestamp": "2026-04-15T18:00:00+00:00"
}
```

## Configuration

| Variable | Description | Default |
|---|---|---|
| HOST | Interface to bind the server to | `0.0.0.0` |
| PORT | Port number to listen on | `5000` |
| VISITS_FILE | Path to the persistent counter file | `/data/visits` |

## Docker

### Build the Image

```bash
docker build -t devops-info-service:latest .
```

### Run the Container

```bash
docker run -d -p 5000:5000 --name devops-service devops-info-service:latest
```

### Persist the Counter with Docker Compose

The Lab 12 compose file is stored in `k8s/docker-compose.yml` and mounts a local volume to `/data`.

```bash
docker compose -f k8s/docker-compose.yml up -d
```

After a few requests to `GET /`, the counter is stored on disk and survives container restarts.

## Example Workflow

```bash
curl http://localhost:5000/
curl http://localhost:5000/
curl http://localhost:5000/visits
```

## Tests

```bash
pytest tests/ -v
```

