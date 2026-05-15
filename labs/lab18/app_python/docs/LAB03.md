# Lab 3 — Continuous Integration (CI/CD)

## Overview

This lab introduces automated testing and CI/CD using GitHub Actions for the FastAPI DevOps Info Service.

The pipeline performs:
- Linting (ruff)
- Unit testing (pytest)
- Security scanning (Snyk)
- Docker image build and push to Docker Hub

## Testing Framework

**Framework used:** pytest

Pytest was chosen because:
- Simple and readable assertions
- Great integration with FastAPI
- Industry standard in modern Python projects

### Tests Implemented

- `GET /` — validates response structure and required fields
- `GET /health` — validates health check structure
- `404 handler` — validates JSON error response

### Run tests locally

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

## CI Workflow

Workflow file:
.github/workflows/python-ci.yml

### Trigger Strategy

Workflow runs on:

* Pull requests affecting app_python/**  
* Push to master affecting app_python/**  

Path filters prevent unnecessary runs in monorepo.

### Versioning Strategy

Strategy: Calendar Versioning (CalVer)

Format:  
YYYY.MM.DD-<run_number>

Docker tags created:

* fayzullin/devops-info-service:<version>

* fayzullin/devops-info-service:latest

This is suitable for continuously deployed services.

## CI Best Practices Applied

Fail fast — Docker build runs only if tests pass.

Dependency caching — pip cache speeds up builds.

Path filters — workflow runs only when app_python changes.

Concurrency control — cancels outdated runs.

## Security Scanning

Snyk is integrated to scan dependencies.
Build fails only on high severity vulnerabilities

## Evidence

GitHub Actions run: (add link after successful run)

Docker Hub: https://hub.docker.com/r/fayzullin/devops-info-service
