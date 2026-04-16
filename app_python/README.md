# DevOps Info Service

## Overview

This Flask service exposes runtime and system information for the DevOps course app. Lab 12 adds a file-backed visit counter, a dedicated `/visits` endpoint, and support for loading non-secret runtime configuration from a JSON file.

## Prerequisites

- Python 3.14+
- `pip`
- Docker and Docker Compose for container-based testing

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the Application

### Local Python run

```bash
python app.py
```

Optional overrides:

```bash
VISITS_FILE=./data/visits APP_CONFIG_PATH=./config/config.json PORT=8080 python app.py
```

### Docker Compose with persistent visits data

```bash
docker compose up --build -d
curl http://localhost:5000/
curl http://localhost:5000/visits
cat ./data/visits
docker compose restart
curl http://localhost:5000/visits
```

The Compose stack bind-mounts `./data` to `/data`, so the visit counter survives container restarts and can be inspected directly on the host.

## API Endpoints

- `GET /` - service, request, runtime, configuration, and visit information
- `GET /health` - health check
- `GET /visits` - current persisted visit count
- `GET /metrics` - Prometheus metrics

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `HOST` | `0.0.0.0` | Flask bind address |
| `PORT` | `5000` | Flask listen port |
| `VISITS_FILE` | `data/visits` | File used to persist the visit counter |
| `APP_CONFIG_PATH` | `config/config.json` | JSON config file path |
| `APP_NAME` | `devops-info-service` | Service name reported by the API |
| `APP_ENV` | `development` | Runtime environment label |
| `LOG_LEVEL` | `INFO` | Application log level |
