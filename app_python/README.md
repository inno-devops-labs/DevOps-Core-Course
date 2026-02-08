# app_python

Minimal FastAPI service for DevOps Labs 2–3 (Docker Containerization and CI/CD).

![CI](https://github.com/Darriyano/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg?branch=lab03)

---

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 5000
```

Endpoints:
- http://localhost:5000/
- http://localhost:5000/health

---

## Local testing (Lab 3)

Unit tests are implemented using **pytest**.

### Setup test environment
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Run tests
```bash
pytest -q
```

Expected output:
```
2 passed in X.XXs
```

Test coverage includes:
- `GET /` — successful response and JSON structure validation
- `GET /health` — health check endpoint
- error case for a non-existing endpoint

---

## Docker

### Build (local image)

From the `app_python/` directory:

```bash
docker build -t devops-course-lab2:local .
```

### Run (local image)

```bash
docker run --rm -p 5000:5000 devops-course-lab2:local
```

---

## Docker Hub (CI/CD)

Docker images are built and published automatically using **GitHub Actions**.

Each successful CI run publishes the image with:
- `latest`
- `YYYY.MM.DD` (Calendar Versioning)

### Pull from Docker Hub

Replace `<dockerhub-username>` with your Docker Hub username:

```bash
docker pull <dockerhub-username>/app_python:latest
docker run --rm -p 5000:5000 <dockerhub-username>/app_python:latest
```

---

## CI/CD Pipeline (Lab 3)

The CI pipeline performs the following steps:
1. Install dependencies
2. Run linting (flake8)
3. Execute unit tests (pytest)
4. Build and push Docker image to Docker Hub
5. Run dependency vulnerability scan (Snyk)

The workflow is triggered on:
- `push` to `lab03`, `master`, or `main`
- `pull_request` events
- changes in `app_python/` or CI workflow files only

---

## Notes

- Local development uses Python virtual environments (PEP 668 compatible).
- CI runs in isolated GitHub Actions runners.
- This service is intentionally minimal and used to demonstrate DevOps practices for the course.
