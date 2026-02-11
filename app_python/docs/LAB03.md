# Lab 3 — Continuous Integration (CI/CD)

## 1. Overview

### Testing Framework: pytest

**Choice:** pytest

**Rationale:**
- Simple syntax with plain `assert` statements
- Rich fixture system for setup/teardown
- Large plugin ecosystem (pytest-cov, pytest-flask)
- Widely used in Python community
- Better DX than unittest (less boilerplate, clearer output)

### What Tests Cover

| Endpoint / Component | Coverage |
|---------------------|----------|
| `GET /` | JSON structure, required fields (service, system, runtime, request, endpoints), data types |
| `GET /health` | Status 200, required fields (status, timestamp, uptime_seconds), timestamp format |
| Error handling | 404 for unknown routes, 405 for wrong HTTP methods |

### CI Workflow Triggers

| Event | Branches | Paths | Action |
|-------|----------|-------|--------|
| **Push** | main, master, lab03 | `app_python/**`, `.github/workflows/python-ci.yml` | Full CI + Docker push |
| **Pull Request** | main, master | `app_python/**`, `.github/workflows/python-ci.yml` | Lint + test only (no Docker push) |

Workflow does **not** run when only docs, labs, or other non-Python files change.

### Versioning Strategy: CalVer (Calendar Versioning)

**Format:** `YYYY.MM.BUILD` (e.g., `2026.02.15`)

**Rationale:**
- No manual version bumps
- Suits continuous deployment
- Clear release date
- Simple to automate in CI

---

## 2. Workflow Evidence

### Successful Workflow Run

- **GitHub Actions:** [Python CI/CD Pipeline](https://github.com/Arino4kaMyr/DevOps-Core-Course/actions/workflows/python-ci.yml)
- [Last successful run](https://github.com/Arino4kaMyr/DevOps-Core-Course/actions/runs/21921525308)

### Tests Passing Locally

```bash
cd app_python
pip install -r requirements.txt -r requirements-dev.txt
pytest -v
```

**Expected output:**
```
tests/test_app.py::TestMainEndpoint::test_main_endpoint_success PASSED
tests/test_app.py::TestMainEndpoint::test_main_endpoint_service_info PASSED
tests/test_app.py::TestMainEndpoint::test_main_endpoint_system_info PASSED
...
tests/test_app.py::TestIntegration::test_content_type_headers PASSED
==================== XX passed in X.XXs ====================
```

### Docker Image on Docker Hub

- **Repository:** https://hub.docker.com/r/mirana18/devops-info-service
- **Pull:** `docker pull mirana18/devops-info-service:latest`

### Status Badge

- Badge in `app_python/README.md`
- Direct link: https://github.com/Arino4kaMyr/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg

---

## 3. Best Practices Implemented

| Practice | Description |
|----------|-------------|
| **Dependency caching** | `cache: 'pip'` in setup-python reduces install time |
| **Docker layer caching** | `cache-from` / `cache-to` for faster image builds |
| **Job dependencies** | Docker job runs only after tests pass (`needs: test`) |
| **Conditional Docker push** | Push only on push events, not on PRs |
| **Path filters** | Workflow runs only when relevant files change |
| **Concurrency** | Cancel older runs on new push (`cancel-in-progress: true`) |
| **Multiple tags** | CalVer + latest + commit SHA for traceability |
| **Secrets** | Credentials via GitHub Secrets, not in code |

**Caching:** Pip caching typically saves ~30–60 seconds per run.

---

## 4. Key Decisions

### Versioning Strategy

CalVer was chosen because the app is deployed continuously and releases are date-based. No manual versioning is needed; CI generates tags automatically.

### Docker Tags

| Tag | Example | Purpose |
|-----|---------|---------|
| Full version | `2026.02.15` | Specific build |
| Month version | `2026.02` | Rolling monthly |
| Latest | `latest` | Most recent |
| Commit SHA | `sha-a1b2c3d` | Traceability |

### Workflow Triggers

Path filters limit runs to changes in Python code or the workflow file. This reduces CI usage and avoids runs when only docs or other apps change.

### Test Coverage

**Tested:**
- `GET /` and `GET /health` (structure, fields, types)
- Error handling (404, 405)
- `format_uptime`, `get_system_info`
- End-to-end response validation

**Not tested:**
- `main` block (app entry point)
- Some error handler paths
- External/logging behavior

**Coverage threshold:** 70% enforced via `--cov-fail-under=70`.

