# Lab 3 — Continuous Integration (CI/CD)

## Task 1 — Unit Testing

### Testing Framework Choice

For this project, pytest was selected as the testing framework.

### Justification:

- Simple and clean syntax compared to built-in unittest
- Excellent integration with FastAPI using TestClient
- Powerful assertion system
- Large ecosystem and community support
- Industry-standard choice for modern Python projects

pytest and required test dependencies were installed in the virtual environment and can be added to dependencies.

### Test Structure

A dedicated `tests/` directory was created(during lab 1, actually):

```
app_python/
    app.py
    tests/
```

It follows standard Python project conventions and allows pytest to discover tests automatically.

### Implemented Unit Tests

Unit tests were written using FastAPI’s `TestClient` to test the application without starting a real HTTP server.

### Tested Endpoints

#### `GET /`

The main service information endpoint is tested for:

- HTTP 200 status code
- Presence of required top-level JSON fields:
  - service
  - system
  - runtime
  - request
  - endpoints
- Correct service metadata:
  - service.name
  - service.framework

This ensures that the API contract is respected and the response structure remains stable.

#### `GET /health`

The health check endpoint is tested for:

- HTTP 200 status code
- Correct health payload structure:
  - status == "healthy"
  - presence of timestamp field
  - presence of uptime_seconds field
- Correct data types of uptime fields

This validates that monitoring and health checks can reliably consume this endpoint.

#### Error and Edge Case Considerations

While the main focus is on successful responses, the test suite validates:

- Correct HTTP status codes
- Required JSON fields exist
- Data types are correct for key fields

The tests are designed to catch:

- Breaking changes in response structure
- Missing fields
- Incorrect service metadata

This provides meaningful tests.

#### How the Application Is Tested Without Running a Server

FastAPI’s `TestClient` is used to simulate HTTP requests directly against the application object:

```
client = TestClient(app)
```

It is used for fast isolated unit tests without binding to network ports or running Uvicorn.

#### Stable Testing

To avoid fragile tests, the following are not asserted with exact values:

- Hostname
- Client IP address
- Timestamp values
- Platform-specific system information

Instead, tests verify existence and structure for better practice with system and environment-dependent data.

### How to Run Tests Locally

From the app_python directory with virtual environment activated:

```
pytest -v
```

#### Example Terminal Output

All tests success:

```
collected 8 items

tests/test_app.py::test_root_endpoint_status_code PASSED                                                         [ 12%]
tests/test_app.py::test_root_endpoint_structure PASSED                                                           [ 25%]
tests/test_app.py::test_service_info PASSED                                                                      [ 37%]
tests/test_app.py::test_health_endpoint_status_code PASSED                                                       [ 50%]
tests/test_app.py::test_health_endpoint_payload PASSED                                                           [ 62%]
tests/test_app.py::test_runtime_fields PASSED                                                                    [ 75%]
tests/test_app.py::test_system_info_fields PASSED                                                                [ 87%]
tests/test_app.py::test_not_found_endpoint PASSED                                                                [100%]
```

## Task 2 — GitHub Actions CI Workflow

This project uses GitHub Actions for CI.

Workflow stages:

- Linting with flake8
- Unit tests with pytest
- Docker image build and push to Docker Hub

### Workflow Trigger Strategy

Triggers: The workflow runs on `push` and `pull_request` events targeting all branches.

Reasoning: This ensures that all new changes are tested and Docker images are built before merging into the main branch. Running on PRs also prevents errors from reaching the master branch.

```
on:
    push:
    pull_request:
```

### Actions

actions/checkout@v4 — Checks out the repository so the workflow can access the code.\
actions/setup-python@v5 — Sets up the required Python version.\
docker/login-action@v3 — Authenticates with Docker Hub using GitHub secrets.\
docker/build-push-action@v6 — Builds and pushes Docker images with proper tags.

Reasoning: These are official, stable, widely used actions that cover testing, linting, and Docker image building without custom scripts. And I use them for other concurrent subject.

### Docker Tagging Strategy

Versioning: Calendar Versioning (CalVer) — `2026.02`.

Tags Created:

- sfedbro/app_python:2026.02 — fixed release version by date
- sfedbro/app_python:latest — always up-to-date version

Reasoning: CalVer is convenient for continuous deployment and easy to track by date. The latest tag simplifies testing and local runs.

```
      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: app_python
          push: true
          tags: |
            ${{ env.IMAGE_NAME }}:${{ steps.version.outputs.VERSION }}
            ${{ env.IMAGE_NAME }}:latest
```

### Successful Workflow Run

GitHub Actions Link: `https://github.com/SfedBro/DevOps-Core-Course/actions/runs/21918200330/job/63291028815#logs`

(is it example or overview?)\
Output Example:

<b>test_and_build</b>\
✔ Set up job\
✔ Checkout repository\
✔ Set up Python\
✔ Install dependencies\
✔ Run flake8\
✔ Run pytest\
✔ Login to Docker Hub\
✔ Set version (CalVer)\
✔ Build and push Docker image\
✔ Post Login to Docker Hub\
✔ Post Set up Python\
✔ Post Checkout repository\
✔ Complete job\

## Task 3 — CI Best Practices & Security

### Status Badge

The workflow has a GitHub Actions status badge showing the current build status. It is visible at the top of the `app_python/README.md` file.
Example Markdown for badge:

[![Python CI + Docker Build](https://github.com/SfedBro/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg?branch=lab03)](https://github.com/SfedBro/DevOps-Core-Course/actions/workflows/python-ci.yml)

### Dependency Caching

I implemented caching for Python dependencies with `actions/cache` to store pip cache between runs and significantly reduce workflow execution time.

Cache key: `${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}`\
Cached path: `~/.cache/pip`

<b>Measured speed improvement:</b>

Without cache: ~20 seconds\
With cache: ~10 seconds (0-1 for caching + 7-14 for installing)

Overall from 25% to 50% time decrease, which shows efficiency of such approach.

### Security Scanning with Snyk

Integrated Snyk using `snyk/actions/python@v1`

Snyk checks for known vulnerabilities in project dependencies.

Environment variable `SNYK_TOKEN` is set via GitHub Secrets.

In total it found 26 low vulnerabilities with no known exploits, and based on not-newest libraries versions(and especially 3.12-slim model for docker), so I did nothing with those(I will consider chanding docker image after finishing this lab).

Result on GitHub:

```
✔ Tested /github/workspace for known issues, no vulnerable paths found.
```

### CI Best Practices Applied

1. Dependency Caching — reduces build times and load on external package repositories.

2. Fail-fast principle — linting, tests, and Snyk scans run before Docker build to avoid building images if code fails quality/security checks.

3. Path filtering — workflow triggers only on changes in app_python/ or workflow file, reducing unnecessary runs.

4. Environment secrets — sensitive information such as Docker Hub credentials and Snyk token are stored in GitHub Secrets.

5. Versioning strategy for Docker images — CalVer tags (YYYY.MM) plus latest tag for reproducibility and continuous deployment.

### Terminal Output / Proof

Workflow runs successfully in GitHub Actions - see it yourself

Docker images are built and pushed with tags:

```
sfedbro/app_python:latest
sfedbro/app_python:2026.02
```

look in screenshots for lab03~ one\
or follow the link: `https://hub.docker.com/repository/docker/sfedbro/app_python/tags/latest/sha256-51af8e10b982eaae63b48c45f6f138cd663f4e8d559fd8158a20e7e0daed94b6` for exact version\
or: `https://hub.docker.com/repository/docker/sfedbro/app_python/general` for python_app in general.

Cached dependencies significantly reduce pipeline time - look in workflows.

Snyk scan completed without vulnerabilities - look in latest forkflow.
