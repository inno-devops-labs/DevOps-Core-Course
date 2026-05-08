# Lab 3 - CI/CD (Python)

## Overview
- **Testing framework:** pytest (simple syntax, fast, good FastAPI support).
- **What is tested:** `/`, `/health`, and 404 handler.
- **CI goal:** run lint + tests on every change; build/push Docker image on main only.
- **Versioning:** CalVer (YYYY.MM.DD) + latest.

## Local Testing
```bash
cd app_python
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

## CI Workflow
- **Workflow:** `.github/workflows/python-ci.yml`
- **Triggers:** push/PR only when `app_python/**` changes.
- **Jobs:**
  - **Test job:** ruff lint + pytest (Python 3.12)
  - **Docker job:** build + push (main/master/lab03)

## Docker Tags (CalVer)
- `kolsmer/devops-app:YYYY.MM.DD`
- `kolsmer/devops-app:YYYY.MM`
- `kolsmer/devops-app:latest`

## Best Practices Applied
- **Dependency caching:** faster runs via `setup-python` pip cache.
- **Job dependency:** Docker push only if tests pass.
- **Concurrency:** cancels outdated runs.
- **Secrets:** Docker Hub and Snyk tokens stored in GitHub Secrets.

## Security Scan (Snyk)
- Action: `snyk/actions/setup@v1.0.0` + `snyk test`
- Threshold: `high`
- Requires `SNYK_TOKEN` secret.

## Required Secrets
- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`
- `SNYK_TOKEN` (optional but recommended)

## Evidence
- **Workflow run:** https://github.com/kolsmer/DevOps-Core-Course/actions/runs/21863701231
- **Docker Hub:** https://hub.docker.com/r/kolsmer/devops-app
- **Docker Hub tags:** `latest`, `2026.02`, `2026.02.10`
- **Cache:** first run `pip cache is not found` (cold cache).
- **Snyk:** Tested 13 dependencies, no vulnerable paths found.
- **Tests output:**
```
================================== test session starts ===================================
platform linux -- Python 3.12.3, pytest-8.3.4, pluggy-1.6.0
rootdir: /home/ramil/Work/DevOps-Core-Course/app_python
plugins: cov-5.0.0, anyio-4.12.1
collected 3 items

tests/test_app.py ...                                                              [100%]

=================================== 3 passed in 0.37s ====================================
```
