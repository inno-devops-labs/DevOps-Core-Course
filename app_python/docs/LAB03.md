# Lab 3 — Continuous Integration

## 1. Overview

**Testing framework:** pytest. Chosen for simple syntax, fixtures, plugin ecosystem (ruff, pytest-cov), and widespread adoption in Python projects.

**Test coverage:** GET `/` (JSON structure, service/system/runtime/request/endpoints), GET `/health` (status, timestamp, uptime), 404 error handling.

**CI triggers:** On push and pull_request to master/main branches.

**Versioning:** CalVer (YYYY.MM). Suitable for continuous deployment; no manual version bumps.

## 2. Workflow Evidence

- **Successful workflow run:** [GitHub Actions](https://github.com/almax07082005/DevOps-Core-Course/actions/workflows/python-ci.yml)
- **Tests passing locally:** `./venv/bin/python -m pytest tests/ -v` from app_python (see below)

```
============================= 13 passed in 0.13s ==============================
```
- **Docker image:** https://hub.docker.com/r/almaxgood/devops-info-service
- **Status badge:** See app_python/README.md

**Screenshot required:** Successful workflow run with green checkmark in the GitHub Actions tab.

## 3. Best Practices Implemented

- **Concurrency cancel:** New runs cancel previous runs on the same branch to avoid redundant work
- **Job dependencies:** Docker build runs only after tests pass
- **Conditional push:** Docker push runs only on direct push to main/master, not on PRs
- **Pip cache:** setup-python with cache reduces install time
- **Docker layer cache:** GHA cache for Docker build layers
- **Snyk:** Dependency scanning (add SNYK_TOKEN secret for full integration)

## 4. Key Decisions

**Versioning:** CalVer (YYYY.MM). Time-based tagging fits continuous deployment; images get tags like `2025.02` and `latest`.

**Docker tags:** `YYYY.MM` (e.g. 2025.02) and `latest`.

**Triggers:** Push and PR to master/main to validate all changes.

**Test coverage:** All HTTP endpoints covered; error handlers tested where practical.

## 5. GitHub Secrets Required

Add these in repo Settings → Secrets and variables → Actions:

- `DOCKERHUB_USERNAME` — Docker Hub username
- `DOCKERHUB_TOKEN` — Docker Hub access token
- `SNYK_TOKEN` — (optional) Snyk API token for vulnerability scanning
