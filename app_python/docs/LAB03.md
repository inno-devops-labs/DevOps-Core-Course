# Lab 03 - Continuous Integration (CI/CD)

## Overview

Testing and CI are added to the Python service. The pipeline runs linting tests, unit tests, coverage tests, Snyk scan, and builds/pushes Docker images using a SemVer strategy.

### Testing

- Text framework - `pytest`: lightweight, fixture support and good plugin ecosystem.
- Tests are in `app_python/tests/` directory: covering `GET /`, `GET /health` endpoints and a 404 case.

Running tests locally:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pytest -q
```

### CI Trigger

Workflow: `.github/workflows/python-ci.yml`
Runs on `push` to `main`/`master`, on `pull_request`, and on `push` of tags matching `v*`.

### Versioning Strategy

Chosen: Semantic Versioning. A tag `v1.2.3` will create a Docker image tagged as `1.2.3`, `1.2`, and `latest`. For non-tagged commits it uses development tag `0.0.0-dev-<run_number>`.

## Workflow Evidence

### Workflow file

`.github/workflows/python-ci.yml`

### Local tests:

```
(venv) cirno@t14-devops:~/Documents/DevOps-Core-Course/app_python$ pytest -q
...                                                                      [100%]
================================ tests coverage ================================
_______________ coverage: platform linux, python 3.12.3-final-0 ________________

Name     Stmts   Miss  Cover
----------------------------
app.py      56      9    84%
----------------------------
TOTAL       56      9    84%
Coverage XML written to file coverage.xml
3 passed in 0.28s
```

# Docker image

https://hub.docker.com/r/iucapstonead/devops-info-service

The image that was built and pushed by the CI/CD is `v0.3.1`.

# Status badge

Added to `app_python/README.md`.

## Best Practices Implemented

### Dependency caching

`actions/cache` caches pip packages based on `requirements.txt` hash. This helps to reduce install time.

### Fail-fast pipeline

Docker build/push runs only after lint and tests succeed.

### Security scanning

Snyk is used in CI to check Python dependencies for known vulnerabilities.

## Key Decisions

### Versioning Strategy

Semantic versioning was chosen because it allows to version with major and minor releases. Making the use of images easier.

### Docker Tags

For tagged releases CI creates `username/devops-info-service:1.2.3`, `username/devops-info-service:1.2`, and `username/devops-info-service:latest`.

### Workflow Triggers

`push` to `main`/`master`, PRs and tag pushes.

### Test Coverage

Unit tests cover main endpoints and a 404 path; coverage is reported via `pytest-cov` and an XML report is produced.
