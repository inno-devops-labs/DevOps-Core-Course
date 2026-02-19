# LAB03

## What I implemented
For this lab, I set up a full basic CI/CD flow for the Python app.
- Testing framework: `pytest`.
- Tests file: `Lab-1/app_python/tests/test_app.py`.
- Covered endpoints and cases:
  - `GET /`
  - `GET /health`
  - `404` error
  - `500` error

## CI workflow
I added one workflow that handles quality checks, security scan, and Docker publishing.
- File: `.github/workflows/python-ci.yml`
- Triggers: `push` and `pull_request` with path filters
- Steps:
  - install dependencies
  - run linter (`ruff`)
  - run tests (`pytest`)
  - run security scan (`Snyk`)
  - build and push Docker image

## Versioning strategy
I chose **CalVer** because it is simple and works well for continuous delivery.
- Docker tags:
  - `YYYY.MM.DD.RUN_NUMBER`
  - `YYYY.MM`
  - `latest`

## Evidence
- Workflow: `https://github.com/Linktur/DevOps-Core-Course/actions/workflows/python-ci.yml`
- Docker Hub: `https://hub.docker.com/r/linktur/devops-lab2/tags`
- Status badge: `Lab-1/app_python/README.md`

Local checks screenshot:
`screenshots/lab03-local-checks.png`

## Local commands
```bash
pip install -r requirements.txt -r requirements-dev.txt
ruff check .
pytest --cov=. --cov-report=term-missing --cov-fail-under=70
```

## Local result
Everything passed locally:
- `ruff`: passed
- `pytest`: 4 passed
- coverage: 94%

## CI best practices used
- Path filters
- Matrix testing (Python 3.11 and 3.12)
- Dependency caching
- Concurrency (cancel outdated runs)
- Job dependencies (`needs`)
- Docker publish only from `main`/`master`

## Final checklist
Before final submission, only these checks are needed:
- Configure GitHub secrets:
  - `DOCKERHUB_USERNAME`
  - `DOCKERHUB_TOKEN`
  - `SNYK_TOKEN`
- Verify one successful green run in GitHub Actions
