# LAB03 — Continuous Integration (CI/CD)

## 1. Overview

### Testing framework choice
I chose **pytest** for unit testing because it has concise syntax, strong fixture support, and is widely used in modern Python projects.

### What the tests cover
The test suite covers both required endpoints and an error case:
- `GET /`: verifies JSON structure and required fields (service/system/runtime/request/endpoints).
- `GET /health`: verifies `status`, `timestamp`, and `uptime_seconds`.
- Error case: `GET /non-existent` returns HTTP 404 with JSON error response.

### How to run tests locally
From repository root:
```bash
PYTHONPATH=. python -m pytest -q
```

### CI workflow triggers
The GitHub Actions workflow runs on `push` and `pull_request` events for the relevant branch(es), so PRs validate code quality while pushes can publish Docker images.

### Versioning strategy (CalVer)
I chose **Calendar Versioning (CalVer)** because this project is a continuously updated service and date-based releases are easy to understand and track over time.
In CI, the Docker image is tagged with at least two tags: a CalVer tag and `latest`.

---

## 2. Workflow proof

### Successful workflow run
GitHub Actions run URL: [Link](https://github.com/GrayMansion/DevOps-Core-Course/actions/runs/21945409220/job/63381609918)

### Local test run output
Paste terminal output showing tests passing locally:
```bash
/mnt/both/ewewe/Innopolis/DevOps-Core-Course main
venv ❯ PYTHONPATH=. python -m pytest -q
...                                                                                                                                                           [100%]
3 passed in 0.68s
```

### Docker Hub image
Docker Hub repo URL: [Link](https://hub.docker.com/repository/docker/graymansion/devops-info-service/general)

Example tags produced by CI:
- `graymansion/devops-info-service:2026.02.4`
- `graymansion/devops-info-service:latest`

### Status badge
A GitHub Actions status badge was added to `app_python/README.md` to show current CI status (passing/failing).

Badge markdown used:
```md
[![python-ci](https://github.com/<USER>/<REPO>/actions/workflows/python-ci.yml/badge.svg)](https://github.com/<USER>/<REPO>/actions/workflows/python-ci.yml)
```

---

## 3. Best practices implemented

### 3.1 Linting
The workflow runs a linter to catch common issues early and enforce consistent code quality.

### 3.2 Fail fast + job dependencies
The pipeline is structured so that Docker build/push happens only if linting and unit tests succeed, which prevents publishing broken images.

### 3.3 Matrix builds
The workflow tests on multiple Python versions using a matrix strategy to reduce the risk of version-specific regressions.

### 3.4 Dependency caching (pip)
Dependency caching is enabled to speed up workflow runs by reusing downloaded packages between runs.

### 3.5 Concurrency / cancel outdated runs
Workflow concurrency is configured to cancel outdated runs when a newer commit is pushed, reducing wasted CI time.

---

## 4. Docker build & tagging

### Docker tags produced by CI
The CI builds and pushes the Docker image to Docker Hub with at least 2 tags (CalVer + latest).

CalVer format used: `<DESCRIBE_FORMAT, e.g., YYYY.MM.<RUN_NUMBER> or YYYY.MM.DD>`

Example produced tag: `<EXAMPLE_TAG>`

### Why CalVer fits this project
CalVer makes it easy to see when an image was built and aligns well with frequent, incremental updates typical for a service.

---

## 5. Snyk security scanning

### Integration approach
Snyk is integrated into the workflow to scan Python dependencies for known vulnerabilities.

### Results
```bash
Tested 12 dependencies for known issues, found 4 issues, 4 vulnerable paths.


Issues to fix by upgrading dependencies:

  Pin idna@3.6 to idna@3.7 to fix
  ✗ Resource Exhaustion [Medium Severity][https://security.snyk.io/vuln/SNYK-PYTHON-IDNA-6597975] in idna@3.6
    introduced by fastapi@0.115.0 > starlette@0.38.6 > anyio@4.12.1 > idna@3.6

  Pin starlette@0.38.6 to starlette@0.49.1 to fix
  ✗ Allocation of Resources Without Limits or Throttling [Medium Severity][https://security.snyk.io/vuln/SNYK-PYTHON-STARLETTE-10874054] in starlette@0.38.6
    introduced by fastapi@0.115.0 > starlette@0.38.6
  ✗ Regular Expression Denial of Service (ReDoS) [High Severity][https://security.snyk.io/vuln/SNYK-PYTHON-STARLETTE-13733964] in starlette@0.38.6
    introduced by fastapi@0.115.0 > starlette@0.38.6
  ✗ Allocation of Resources Without Limits or Throttling [High Severity][https://security.snyk.io/vuln/SNYK-PYTHON-STARLETTE-8186175] in starlette@0.38.6
    introduced by fastapi@0.115.0 > starlette@0.38.6



Organization:      graymansion
Package manager:   pip
Target file:       app_python/requirements.txt
Project name:      app_python
Open source:       no
Project path:      /home/runner/work/DevOps-Core-Course/DevOps-Core-Course
Licenses:          enabled
```

---

## 6. Key decisions

### Versioning strategy
I used CalVer instead of SemVer because the service is deployed continuously and a date-based version makes releases easy to track without implying API-breaking semantics.

### Workflow triggers
I trigger CI on pushes/PRs to ensure code is validated before merge and to automate Docker publishing on pushes when appropriate.

### Docker publishing rules
Docker images are only pushed when CI succeeds, preventing broken images from being published.

### Test coverage (scope)
Tests validate API contract and response structure rather than machine-specific values like hostname, which makes them stable across environments and CI runners.

---

## 7. Challenges & solutions

### Docker Hub credentials in CI
Challenge: The Docker login step failed until Docker Hub credentials were added securely via GitHub Secrets.

Solution: Added `DOCKERHUB_USERNAME` and a Docker Hub access token as repository secrets and referenced them in the workflow.
