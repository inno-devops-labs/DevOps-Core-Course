## Overview

[![Python CI/CD](https://github.com/InnoNodo/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)](https://github.com/IU-DevOps-Course/DevOps-Core-Course/actions/workflows/python-ci.yml)
[![Go CI/CD](https://github.com/InnoNodo/DevOps-Core-Course/actions/workflows/go-ci.yml/badge.svg)](https://github.com/IU-DevOps-Course/DevOps-Core-Course/actions/workflows/go-ci.yml)
[![Coverage Status](https://codecov.io/gh/InnoNodo/DevOps-Core-Course/branch/lab03/graph/badge.svg)](https://app.codecov.io/github/InnoNodo/DevOps-Core-Course/tree/lab03)

This Python application provides a RESTful service that delivers system and service information through health check endpoints.
It also persists visit counts to a file so the counter survives container restarts when `/data` is mounted.

## Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

## Installation

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

Start the application with default settings:
```bash
python app.py
```

Or specify a custom port:
```bash
PORT=8080 python app.py
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Service, system, config, and visit information. Each request increments the persisted visits counter |
| GET | `/visits` | Current persisted visits counter |
| GET | `/health` | Health check status |
| GET | `/ready` | Readiness check status |
| GET | `/metrics` | Prometheus metrics |

## Configuration

Configure the application using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `5000` | Server port |
| `HOST` | `0.0.0.0` | Server host address |
| `VISITS_FILE` | `/data/visits` | Path to the persisted visits counter file |
| `APP_CONFIG_PATH` | `/config/config.json` | Path to JSON configuration loaded at runtime |
| `APP_ENV` | `dev` | Environment name exposed by the service |
| `LOG_LEVEL` | `info` | Application log level |

## Visits Persistence

The root endpoint increments a counter stored in `VISITS_FILE`. The `/visits` endpoint returns the current value without incrementing it.

Implementation details:
- The counter is loaded from disk on demand and defaults to `0` when the file does not exist.
- Updates are serialized with a process-local lock.
- Writes use a temporary file plus atomic rename to reduce corruption risk.

Example:
```bash
curl http://127.0.0.1:5000/
curl http://127.0.0.1:5000/
curl http://127.0.0.1:5000/visits
```

Expected result:
```json
{"visits": 2, "storage": "/data/visits"}
```

## Testing

### Testing Framework: pytest

This project uses **pytest** for comprehensive unit testing. Pytest was chosen for its:
- Simple, intuitive syntax for writing tests
- Powerful fixtures system for test setup and teardown
- Excellent plugin ecosystem and integration with FastAPI
- Rich assertion introspection for clear test failures
- Easy test discovery and parametrization

### Test Coverage

The test suite includes **25 comprehensive tests** covering:

**GET / Endpoint (11 tests)**
- HTTP status code verification (200)
- JSON response validation
- Response structure (service, system, runtime, request sections)
- Service metadata validation (name, version, framework)
- System information validation (hostname, platform, CPU count, Python version)
- Runtime information (uptime, timestamp in ISO format, timezone)
- Request data capture (client IP, user agent, method, path)
- Custom user agent handling
- Uptime progression across multiple calls
- Hostname consistency

**GET /health Endpoint (14 tests)**
- HTTP status code verification (200)
- JSON response structure validation
- Required fields (status, timestamp, uptime_seconds)
- Health status is "healthy"
- Timestamp validation (ISO format and recency)
- Uptime validation (integer, non-negative)
- Response size verification
- Uptime progression across requests
- Consistency across multiple calls
- Deterministic responses
- No authentication requirement

### Running Tests Locally

Install development dependencies (includes pytest):
```bash
pip install -r requirements-dev.txt
```

Run all tests with verbose output:
```bash
pytest tests/ -v
```

Run tests with coverage report:
```bash
pip install pytest-cov
pytest tests/ -v --cov=. --cov-report=html
```

Run specific test file:
```bash
pytest tests/test_get_health.py -v
pytest tests/test_get_root.py -v
```

Run specific test class or method:
```bash
pytest tests/test_get_health.py::TestHealthEndpoint -v
pytest tests/test_get_health.py::TestHealthEndpoint::test_health_endpoint_returns_200_status -v
```

### Test Results

All tests pass successfully:
```
============================= 25 passed in 0.39s =============================
```

### Test Structure

```
tests/
├── conftest.py              # pytest fixtures and configuration
├── test_get_health.py       # Health endpoint tests
└── test_get_root.py         # Root endpoint tests
```

**conftest.py**: Provides the `client` fixture, which creates a FastAPI TestClient for making requests to the application without starting a real server.

**test_get_root.py**: Tests for the main `/` endpoint including service information, system details, and runtime metrics.

**test_get_health.py**: Tests for the `/health` endpoint including status checks, timestamp validation, and uptime tracking.

## Continuous Integration / Continuous Delivery (CI/CD)

This project uses **GitHub Actions** for automated testing and Docker image building. See [CI_CD.md](../CI_CD.md) for comprehensive documentation.

### Workflow Overview

The GitHub Actions workflow (`.github/workflows/python-ci.yml`) runs automatically on:
- Push to `main`, `master`, or `develop` branches
- Pull requests to `main` or `master`

**Pipeline Stages:**
1. **Test & Lint** - Runs pytest and ruff code quality checks
2. **Docker Build & Push** - Builds and pushes to Docker Hub (main branch only)
3. **Notification** - Provides status summary

### Versioning Strategy: Calendar Versioning (CalVer)

Images are tagged using **Calendar Versioning** format: `YYYY.MM.DD`

Example tags for a build on February 11, 2024:
- `username/devops-info-service:2024.02.11` - Date version
- `username/devops-info-service:2024.02.11-a1b2c3d` - With commit SHA
- `username/devops-info-service:latest` - Latest build

### Setting Up GitHub Actions

1. **Fork and clone** this repository to your GitHub account
2. **Create Docker Hub access token:**
   - Go to hub.docker.com → Account Settings → Security
   - Click "New Access Token"
   - Copy the token (save securely)
3. **Add GitHub secrets:**
   - Go to repository Settings → Secrets and variables → Actions
   - Add `DOCKER_USERNAME` (your Docker Hub username)
   - Add `DOCKER_PASSWORD` (the access token from step 2)
4. **Push to trigger workflow:**
   ```bash
   git push origin main
   ```
5. **Monitor in GitHub Actions tab** to see workflow execution

### Local Development Equivalent

To replicate the CI workflow locally:

```bash
# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Run linter
ruff check app_python

# Run tests
pytest tests/ -v

# Build Docker image
docker build -t devops-info-service:local app_python
```

## Docker Usage

This application can be run inside a Docker container.

### Build the image locally
Use the Dockerfile to build the image from the project source.

Pattern:
```bash
docker build -t <image-name> app_python
```

### Run the container
Run the container interactively to start the application.

Pattern:
```bash
docker run -p <port:port> -it <image-name>
```

### Run with Docker Compose and a persistent volume

The repository includes [docker-compose.yml](/home/nodo/DevOps-Core-Course/app_python/docker-compose.yml) for local persistence testing.

```bash
cd app_python
docker compose up -d
curl http://127.0.0.1:5000/
curl http://127.0.0.1:5000/visits
cat data/visits
docker compose restart
curl http://127.0.0.1:5000/visits
```

What this does:
- Uses the local `devops-info-service:latest` image and bind-mounts `app.py` so the current workspace code runs immediately
- Mounts `./data` to `/data` so the visits file survives restarts
- Mounts `./config/config.json` to `/config/config.json`
- Keeps the image immutable while externalizing runtime state and config

If the image is not present yet, build or pull it first:

```bash
docker build -t devops-info-service:latest .
```

### Pull from Docker Hub
The image is automatically built and pushed by GitHub Actions.

Pattern:
```bash
docker pull <dockerhub-username>/devops-info-service:latest
docker run -p 5000:5000 <dockerhub-username>/devops-info-service:latest
```

### Available Tags

Pull specific versions using the CalVer tags generated by CI/CD:
```bash
# Pull latest
docker pull <dockerhub-username>/devops-info-service:latest

# Pull specific date version
docker pull <dockerhub-username>/devops-info-service:2024.02.11

# Pull specific build with commit
docker pull <dockerhub-username>/devops-info-service:2024.02.11-a1b2c3d
```
