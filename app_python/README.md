# DevOps Info Service (Python / Flask)

[![python-ci](https://github.com/egraPA006/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)](https://github.com/egraPA006/DevOps-Core-Course/actions/workflows/python-ci.yml)
![version](https://img.shields.io/github/v/tag/egraPA006/DevOps-Core-Course?sort=semver)

## Overview

DevOps Info Service is a small HTTP web service that exposes information
about: - the service itself (metadata) - the host system and runtime
environment - incoming HTTP request context

It also provides a health-check endpoint intended for monitoring systems
and container orchestrators (Docker, Kubernetes).

This repository is used across DevOps labs:
 - **Lab 1:** endpoints +
documentation
 - **Lab 2:** Docker containerization 
 - **Lab 3:** CI/CD
(lint + tests + Docker build/push on version tags)

> Lab reports live in `app_python/docs/`. This README is the repository
> entry point.

## Prerequisites

-   Python **3.11+** (CI uses **Python 3.13**)
-   `pip`
-   (recommended) virtual environment (`venv`)
-   Docker (optional, for container run)

## Project Structure (Python app)

    app_python/
    ├── app.py
    ├── Dockerfile
    ├── requirements.txt
    ├── requirements-dev.txt
    ├── pytest.ini
    └── tests/
        ├── conftest.py
        └── test_endpoints.py

## Installation

``` bash
cd app_python
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Running the Application

### Default run

``` bash
python app.py
```

Service will be available at:

    http://0.0.0.0:5000

### Custom configuration

``` bash
PORT=8080 python app.py
HOST=127.0.0.1 PORT=3000 python app.py
DEBUG=true python app.py
```

## API Endpoints

### `GET /`

Returns service metadata, system information, runtime details, and
request context.

Example:

``` bash
curl -s http://127.0.0.1:5000/ | python -m json.tool
```

### `GET /health`

Health-check endpoint used for monitoring and readiness/liveness probes.

Example:

``` bash
curl -s http://127.0.0.1:5000/health | python -m json.tool
```

### `GET /visits`

Returns the current persistent visit count.

Example:

``` bash
curl -s http://127.0.0.1:5000/visits | python -m json.tool
```

## Configuration

The application is configured via environment variables:

  Variable   Default     Description
  ---------- ----------- --------------------------------------------
  `HOST`     `0.0.0.0`   Server bind address
  `PORT`     `5000`      TCP port
  `DEBUG`    `False`     Enables Flask debug mode and debug logging
  `APP_CONFIG_PATH` `/config/config.json` JSON config file path
  `VISITS_FILE` `data/visits` Persistent visit counter file
  `APP_ENV`  `dev`       Runtime environment label
  `LOG_LEVEL` `INFO`     Log level metadata exposed by the app
  `APP_DISPLAY_NAME` `devops-info-service` Service name override

## Persistent Visits Counter

Every `GET /` request increments a file-backed counter. The application
loads the existing value on startup, stores updates in `VISITS_FILE`,
and exposes the current count through `GET /visits`.

Quick local check:

``` bash
cd app_python
python app.py
curl -s http://127.0.0.1:5000/
curl -s http://127.0.0.1:5000/visits | python -m json.tool
cat data/visits
```

## Testing & Lint (Lab 3)

Tools used: - **pytest** (unit tests) - **flake8** (lint)

Run locally:

``` bash
cd app_python
pytest -q
flake8 .
```

## CI/CD (Lab 3)

### Workflow summary

GitHub Actions workflow: `.github/workflows/python-ci.yml`

Triggers: - `push` / `pull_request` only when files under
`app_python/**` change (or when the workflow file itself changes) -
manual trigger via `workflow_dispatch`

Pipeline stages: 1. **test job** - Python 3.13 - installs dependencies -
runs `flake8` - runs `pytest` - caches pip dependencies 2.
**docker-release job** (runs only if tests passed) - triggers only on
git tags matching `v*` (e.g. `v1.2.3`) - builds and pushes Docker image
to Docker Hub - uses BuildKit cache (GHA cache)

### Docker image & tags

Docker Hub image: - `egrapa/devops-core-course-lab2`

On tag `vX.Y.Z`, CI pushes: - `egrapa/devops-core-course-lab2:X.Y.Z` -
`egrapa/devops-core-course-lab2:X.Y` -
`egrapa/devops-core-course-lab2:latest`

### How to publish a release (SemVer)

Create and push a version tag:

``` bash
git tag v1.2.3
git push origin v1.2.3
```

After that, `docker-release` will build and push the image tags listed
above.

## Docker

### Build (local)

``` bash
docker build -t egrapa/devops-core-course-lab2:dev app_python/
```

### Run

``` bash
docker run --rm -p 8080:5000 --name devops-info egrapa/devops-core-course-lab2:dev
```

Test from host:

``` bash
curl -s http://127.0.0.1:8080/health | python -m json.tool
curl -s http://127.0.0.1:8080/ | python -m json.tool
```

### Compose Persistence Check

The monitoring compose stack now bind-mounts `monitoring/data` into the
app container so the visits file survives container restarts.

``` bash
mkdir -p monitoring/data
docker compose -f monitoring/docker-compose.yml up -d app-python
curl -s http://127.0.0.1:8000/
curl -s http://127.0.0.1:8000/
curl -s http://127.0.0.1:8000/visits | python -m json.tool
cat monitoring/data/visits
docker compose -f monitoring/docker-compose.yml restart app-python
curl -s http://127.0.0.1:8000/visits | python -m json.tool
```

## Notes

-   All timestamps are returned in UTC
-   Uptime is calculated since process start
-   Client IP is resolved via `X-Forwarded-For` (if present) or
    `remote_addr`
-   Error responses (404 / 500) are returned in JSON format

## Development Notes

-   Code follows PEP 8 style guidelines
-   Dependencies are pinned for reproducibility
-   Logging uses Python standard `logging`
