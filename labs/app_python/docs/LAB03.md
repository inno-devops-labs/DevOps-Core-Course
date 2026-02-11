# Lab 3 — CI/CD

## 1. Overview

### Testing Framework — pytest

I chose **pytest** because it is the most popular Python testing framework. It has simple syntax, no need for boilerplate classes, and works great with FastAPI's `TestClient`. I also added `ruff` as a linter since it is fast and catches common issues.

### What is tested

- `GET /` — checks status code 200, verifies JSON structure has all sections (`service`, `system`, `runtime`, `request`, `endpoints`), checks correct field values and types
- `GET /health` — checks status 200, verifies `status` is `"healthy"`, `timestamp` and `uptime_seconds` fields exist and have correct types
- `GET /nonexistent` — checks 404 status code and error response

Total: **13 tests** covering both endpoints and error handling.

### CI Workflow Triggers

The workflow runs on:
- Push to `lab03` or `master` branches (only when `labs/app_python/**` files change)
- Pull requests to `master` (same path filter)

This means changing docs or Go app files will NOT trigger the Python CI.

### Versioning Strategy — CalVer

I chose **Calendar Versioning** (CalVer) with format `YYYY.MM.DD`. Reasons:
- This is a web service, not a library, so "breaking changes" idea does not apply much
- CalVer makes it easy to know when the image was built just by looking at the tag
- Simple to generate automatically in CI with `date +%Y.%m.%d`

Docker images get two tags: `2026.02.11` (date) + `latest`.

## 2. Workflow Evidence

- **Successful workflow run:** https://github.com/blxxdclxud/DevOps-Core-Course/actions/workflows/python-ci.yml
- **Docker Hub image:** https://hub.docker.com/r/blxxdclxud/devops-info-service
- **Status badge:** visible in the [README](../README.md) at the top

### Tests passing locally

```
tests/test_app.py::test_root_status_code PASSED       [  7%]
tests/test_app.py::test_root_has_service_section PASSED [ 15%]
tests/test_app.py::test_root_has_system_section PASSED [ 23%]
tests/test_app.py::test_root_has_runtime_section PASSED [ 30%]
tests/test_app.py::test_root_has_request_section PASSED [ 38%]
tests/test_app.py::test_root_has_endpoints_list PASSED [ 46%]
tests/test_app.py::test_root_returns_json PASSED      [ 53%]
tests/test_app.py::test_health_status_code PASSED     [ 61%]
tests/test_app.py::test_health_status_healthy PASSED  [ 69%]
tests/test_app.py::test_health_has_timestamp PASSED   [ 76%]
tests/test_app.py::test_health_has_uptime PASSED      [ 84%]
tests/test_app.py::test_not_found_returns_404 PASSED  [ 92%]
tests/test_app.py::test_not_found_returns_error_json PASSED [100%]

13 passed in 0.63s
```

## 3. Best Practices Implemented

- **Dependency caching:** `actions/setup-python` with `cache: 'pip'` — avoids re-downloading packages every run, saves about 20-30 seconds
- **Job dependencies:** Docker build & push only runs if tests pass — no broken images get pushed
- **Concurrency control:** `cancel-in-progress: true` — if I push twice quickly, the old run gets cancelled, saves CI minutes
- **Path-based triggers:** workflow only runs when Python app files change — no wasted runs when editing docs or Go code
- **Conditional Docker push:** `if: github.event_name == 'push'` — PRs only run tests, no accidental pushes to Docker Hub
- **Snyk scanning:** checks dependencies for known vulnerabilities. Using `continue-on-error: true` so it warns but does not block the build (some vulns might not have fixes yet)

## 4. Key Decisions

- **Versioning Strategy:** I went with CalVer (`2026.02.11` format). My app is a web service deployed continuously, so knowing the build date is more useful than semver numbers. There are no "breaking changes" in a service that just shows system info.

- **Docker Tags:** Each push creates two tags — a CalVer date tag (e.g., `2026.02.11`) and `latest`. The date tag gives you a stable reference point, and `latest` always points to the newest build.

- **Workflow Triggers:** Push to `lab03`/`master` + PRs to `master`. Path filtering to `labs/app_python/**` so only relevant changes trigger the pipeline. This is efficient for a monorepo.

- **Test Coverage:** All main endpoints are tested (GET `/` and GET `/health`) plus 404 error handling. What is NOT tested: 500 error handler (hard to trigger without mocking), the `if __name__ == '__main__'` block (that is just the server startup, not worth testing).
