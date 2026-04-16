# Lab 1 — DevOps Info Service: Implementation Report

**Student:** Danil Fishchenko  
**Date:** April 5, 2026  
**Framework:** Flask 3.1.0  
**Language:** Python 3.11+

## Framework Selection

### Chosen Framework: Flask

Flask was selected because Lab 1 needs a small HTTP service with explicit control over routes, JSON responses, and configuration without the heavier abstractions of a full-stack framework.

### Comparison With Alternatives

| Framework | Strengths | Tradeoffs |
|-----------|-----------|-----------|
| Flask | Minimal, easy to reason about, fast to bootstrap, mature ecosystem | Less built-in validation and scaffolding |
| FastAPI | Excellent validation, async-first design, automatic OpenAPI docs | More framework machinery than required for this lab |
| Django | Batteries included, great for larger web apps | Too heavy for a two-endpoint info service |

### Why Flask Fits Lab 1

- The assignment only needs a focused web service with a couple of JSON endpoints.
- Flask keeps the implementation readable and easy to extend in later labs.
- Official Flask JSON support and error handlers make it straightforward to keep the API consistent.

## Best Practices Applied

### 1. Small Helper Functions

The application separates concerns into dedicated helpers such as `get_system_info()`, `get_runtime_info()`, `get_request_info()`, and `get_endpoints_list()`. This keeps the route handlers short and testable.

### 2. Environment-Based Configuration

The service reads `HOST`, `PORT`, `DEBUG`, and `LOG_LEVEL` from environment variables. Lab 1 source runs default to `0.0.0.0:5000`, while later containerized labs override `PORT=3000` explicitly to keep the broader repository consistent.

### 3. Consistent JSON Error Responses

The app returns JSON for both `404 Not Found` and `405 Method Not Allowed` instead of default HTML error pages. That keeps the API predictable for CLI users, tests, and future automation.

### 4. Structured Logging

Application logs are emitted as JSON records with timestamp, level, message, and request metadata. This is not required by the minimum Lab 1 spec, but it is a useful production-friendly extension that does not change the Lab 1 contract.

### 5. Automated Validation

The Python app has unit tests for successful responses, error handling, and the cumulative `/metrics` endpoint that exists for later labs. Linting is enforced with Ruff.

## API Documentation

### `GET /`

Returns:
- `service`: service name, version, description, framework
- `system`: hostname, platform, platform version, architecture, CPU count, Python version
- `runtime`: uptime, human-readable uptime, current UTC time, timezone
- `request`: client IP, user agent, method, path
- `endpoints`: endpoint descriptions

Example command:

```bash
curl http://127.0.0.1:5000/
```

### `GET /health`

Returns:
- `status`
- `timestamp`
- `uptime_seconds`

Example command:

```bash
curl http://127.0.0.1:5000/health
```

### Error Handling Example

Unsupported methods return JSON as well:

```bash
curl -i -X POST http://127.0.0.1:5000/
```

## Testing Evidence

### Automated Checks

Commands used during verification on April 5, 2026:

```bash
.venv/bin/python -m ruff check .
.venv/bin/python -m pytest tests/
```

Observed result:
- `ruff`: passed
- `pytest`: `20 passed`
- coverage: `97%`

### Manual Checks

Service launch used for local smoke testing:

```bash
HOST=127.0.0.1 PORT=5051 .venv/bin/python app.py
```

Manual requests executed:

```bash
curl http://127.0.0.1:5051/
curl http://127.0.0.1:5051/health
curl -i -X POST http://127.0.0.1:5051/
curl -i http://127.0.0.1:5051/nonexistent
```

Validated manually:
- `GET /` returns the expected nested JSON structure
- `GET /health` returns `200 OK` and a healthy status payload
- `POST /` returns JSON `405 Method Not Allowed`
- unknown routes return JSON `404 Not Found`

### Screenshots

Required screenshot files are present:
- `screenshots/01-main-endpoint.png`
- `screenshots/02-health-check.png`
- `screenshots/03-formatted-output.png`

These screenshots capture successful endpoint responses from a local run. Some screenshots use port `3000`, which is also supported through the `PORT` environment variable.

## Challenges & Solutions

### Challenge 1: Lab 1 Defaults vs Later Course Conventions

Lab 1 examples use port `5000`, while later containerized labs in this repository standardize on `3000`.

**Solution:** the source application now defaults to `5000` for Lab 1 correctness, and the Docker image explicitly sets `PORT=3000` so later labs keep working.

### Challenge 2: Consistent API Error Format

Flask automatically returns an HTML page for unsupported methods unless a custom handler is added.

**Solution:** a JSON `405` handler was added so API clients always receive machine-readable error payloads.

### Challenge 3: Keeping Documentation Honest in a Cumulative Repository

The repository already contains later-lab functionality such as `/metrics`. Lab 1 documentation must stay accurate without pretending those additions are part of the original minimum scope.

**Solution:** the report distinguishes between the required Lab 1 endpoints and later-lab cumulative enhancements.

## GitHub Community

Starring repositories matters because it helps you bookmark valuable projects, signals appreciation to maintainers, and makes useful tools easier to discover across the community. Following developers is useful because it improves awareness of peers' work, exposes you to implementation patterns, and supports collaboration and professional growth.

The required star and follow actions for Lab 1 must be completed on the student's GitHub account before submission, because they cannot be verified from this local repository alone.
