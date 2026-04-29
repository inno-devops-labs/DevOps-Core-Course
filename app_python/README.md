# DevOps Info Service (FastAPI)

![CI](https://github.com/lanebo1/DevOps-Core-Course/workflows/Python%20CI/badge.svg)

## Overview

A small web service that reports service metadata, system details, runtime uptime, and request information. Built as the foundation for future DevOps labs.

## Prerequisites

- Python 3.11+

## Installation

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the Application

### Local Development

```bash
python3 app.py
```

### Docker

Build the image locally:

```bash
docker build -t devops-info-service .
```

Run a container:

```bash
docker run -p 5000:5000 devops-info-service
```

Pull from Docker Hub:

```bash
docker pull lanebo1/devops-info-service
docker run -p 5000:5000 lanebo1/devops-info-service
```

## Testing

Install test dependencies and run the test suite:

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
```

The test suite covers:
- Response status codes and content types
- JSON response structure validation
- System information fields presence
- Error handling for invalid endpoints
- Health check functionality

## API Endpoints

- `GET /` - Service and system information (increments the persisted visit counter)
- `GET /visits` - Current visit counter (stored under `VISITS_FILE_PATH`)
- `GET /health` - Health check

## Visit counter and Docker Compose

The service persists a hit counter on disk (default path `/data/visits`). Each `GET /` increments the counter; `GET /visits` returns the current value without incrementing.

Local persistence with Compose uses a **named Docker volume** (`visits_data`) mounted at `/data`, so the non-root app user (UID 999) can write the visits file.
```bash
docker compose up --build
```

## Configuration

| Variable            | Default       | Description                          |
| ------------------- | ------------- | ------------------------------------ |
| `HOST`              | `0.0.0.0`     | Bind address                        |
| `PORT`              | `5000`        | Server port                         |
| `DEBUG`             | `False`       | Enables auto-reload                 |
| `VISITS_FILE_PATH`  | `/data/visits`| File used for the visit counter     |
| `APP_ENV`           | *(unset)*   | Optional label injected via Kubernetes ConfigMap |
| `LOG_LEVEL`         | `INFO`        | Root logging level name             |
