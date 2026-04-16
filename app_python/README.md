# DevOps Info Service

[![CI/CD Pipeline](https://github.com/pav0rkmert/DevOps-Core-Course/workflows/Python%20CI%2FCD%20Pipeline/badge.svg)](https://github.com/pav0rkmert/DevOps-Core-Course/actions)
[![Coverage](https://codecov.io/gh/pav0rkmert/DevOps-Core-Course/branch/main/graph/badge.svg)](https://codecov.io/gh/pav0rkmert/DevOps-Core-Course)

A Python Flask service that exposes runtime metadata, health checks, Prometheus metrics, and a persisted visit counter. The service is used across the DevOps course labs and now supports file-based configuration and file-backed persistence for Kubernetes ConfigMaps and PVCs.

## Overview

The service provides:
- service metadata and runtime details
- host system information
- request details for the current HTTP call
- a `/health` endpoint for probes
- a `/metrics` endpoint for Prometheus
- a persisted `/visits` counter stored in a file
- optional JSON configuration loaded from `APP_CONFIG_FILE`

## Prerequisites

- Python 3.11 or higher
- pip

## Installation

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the Application

### Development Mode

```bash
python app.py
```

The service listens on `http://0.0.0.0:5000` by default.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Host address to bind |
| `PORT` | `5000` | Port number |
| `DEBUG` | `False` | Enable Flask debug mode |
| `LOG_LEVEL` | `INFO` | JSON log level |
| `VISITS_FILE_PATH` | `/data/visits` | File used to persist the visit counter |
| `APP_CONFIG_FILE` | `/config/config.json` | Optional JSON config mounted from a ConfigMap |

### Examples

```bash
PORT=8080 python app.py
HOST=127.0.0.1 PORT=3000 python app.py
DEBUG=true LOG_LEVEL=DEBUG python app.py
VISITS_FILE_PATH=./data/visits APP_CONFIG_FILE=./config/config.json python app.py
```

## Docker

### Build the Image

```bash
docker build -t devops-info-service:lab12 .
```

### Run with a Persistent Counter

```bash
docker run -d \
  -p 5005:5000 \
  -e VISITS_FILE_PATH=/data/visits \
  -v "$(pwd)/data:/data" \
  --name devops-app \
  devops-info-service:lab12
```

### Local Persistence Test with Docker Compose

The repository includes [`docker-compose.yml`](docker-compose.yml) for Lab 12:

```bash
docker compose up --build -d
curl http://localhost:5005/ | jq '.visits'
curl http://localhost:5005/ | jq '.visits'
cat ./data/visits
docker compose down
docker compose up -d
curl http://localhost:5005/visits | jq
```

The bind mount `./data:/data` preserves the counter across container restarts.

## API Endpoints

### `GET /`

Returns service metadata, runtime details, loaded file configuration, and increments the persisted visit counter.

Example:

```bash
curl http://localhost:5000/ | jq
```

Response excerpt:

```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Flask"
  },
  "configuration": {
    "loaded": true,
    "path": "/config/config.json",
    "data": {
      "application": {
        "name": "devops-info-service",
        "environment": "dev"
      }
    }
  },
  "visits": {
    "count": 3,
    "file_path": "/data/visits"
  }
}
```

### `GET /visits`

Returns the current persisted visit counter without incrementing it.

```bash
curl http://localhost:5000/visits | jq
```

### `GET /health`

Returns probe-friendly application health information.

```bash
curl http://localhost:5000/health | jq
```

### `GET /metrics`

Returns Prometheus metrics.

```bash
curl http://localhost:5000/metrics
```

## Project Structure

```text
app_python/
├── app.py
├── Dockerfile
├── docker-compose.yml
├── README.md
├── requirements.txt
├── tests/
└── docs/
```

## Testing

```bash
./venv/bin/pytest
./venv/bin/pytest --cov=app --cov-report=term-missing
```

The test suite covers:
- `GET /`, `GET /health`, and `GET /visits`
- persisted counter creation and increment behavior
- config file loading and fallback when the file is missing
- 404 handling and unsupported HTTP methods

## Notes

- Visit persistence is intentionally file-based for Lab 12 so it can be backed by a Docker bind mount or a Kubernetes PVC.
- The application uses a thread lock plus atomic file replacement (`os.replace`) to avoid partial writes.
- The current persistence design assumes a single writer pod. The Helm chart for Lab 12 therefore defaults to `replicaCount: 1`.
