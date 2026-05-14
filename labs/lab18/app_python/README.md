# DevOps Info Service

[![Python CI/CD](https://github.com/ebortsov/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg?branch=lab03)](https://github.com/ebortsov/DevOps-Core-Course/actions/workflows/python-ci.yml)

This project delivers a Python-based web service that reports detailed system and runtime information. It will be expanded across the labs to include health monitoring, containerization, CI/CD, and persistence. The app uses FastAPI.

## Structure
- `app.py` — service entry point (framework selection in Task 1.2)
- `requirements.txt` — Python dependencies
- `requirements-dev.txt` — development dependencies (testing tools)
- `docs/` — lab notes and screenshots
- `tests/` — endpoint unit tests

## Getting Started
1. Install dependencies: `python3 -m pip install -r requirements.txt`.
2. Run the app: `python3 app.py` (defaults to host `0.0.0.0` and port `5000`).
3. Override configuration with env vars: `HOST=127.0.0.1 PORT=8080 DEBUG=true python3 app.py` (reload follows `DEBUG`).
4. The visits counter is persisted to `VISITS_FILE_PATH` (defaults to `/tmp/devops-info-service/visits` for local runs).
5. Optional deployment metadata can be overridden with env vars such as `SERVICE_NAME`, `SERVICE_VERSION`, `SERVICE_DESCRIPTION`, `SERVICE_VARIANT`, and `APP_CONFIG_PATH`.

Available endpoints:
- `GET /` - service and system information
- `GET /health` - liveness probe
- `GET /ready` - readiness probe
- `GET /visits` - current persistent visit counter
- `GET /metrics` - Prometheus metrics

## Testing (Lab 3 Task 1)
- Framework: `unittest` (Python standard library)
- Why: zero external dependency overhead and reliable route-level endpoint testing via in-memory ASGI requests.

Run tests locally:
1. Install runtime and test dependencies:
   - `python3 -m pip install -r requirements.txt`
   - `python3 -m pip install -r requirements-dev.txt`
2. Run all tests:
   - `python3 -m unittest -v`

Current test scope:
- `GET /` response structure, field presence, and type checks
- `GET /health` response checks
- Error cases (`404 Not Found`, `405 Method Not Allowed`)

## Docker
- Build image: `docker build -t <user>/<repo>:<tag> .`
- Run container: `docker run -d -p 5000:5000 --name devops-info -e HOST=0.0.0.0 -e PORT=5000 <user>/<repo>:<tag>`
- Pull from Hub: `docker pull <user>/<repo>:<tag>`
- The image runs as a fixed non-root UID/GID (`10001:10001`) to stay compatible with Kubernetes `runAsNonRoot` policies.
- Lab 12 local persistence flow:
  - Start the stack: `docker compose up --build`
  - The compose service runs as `root` locally so it can initialize the bind-mounted `./data` directory; the Kubernetes chart keeps the non-root `10001` runtime with `fsGroup`
  - Hit `GET /` a few times
  - Check the host-side file: `cat ./data/visits`
  - Restart the container with `docker compose restart`
  - Confirm `GET /visits` still returns the previous count
