# LAB03 — Continuous Integration (CI/CD)

## 1. Overview

### Testing Framework

**pytest** — Chosen for its simple syntax, strong fixture support, and wide adoption. It integrates well with Flask's test client and supports clear assertions.

### Test Coverage

- **GET /** — Status 200, JSON structure, required fields (service, system, runtime, request, endpoints), data types
- **GET /health** — Status 200, `status=healthy`, `uptime_seconds`, `timestamp`
- **404** — Non-existent paths return 404 with error structure
- **Request context** — User-Agent and path reflected in response

### CI Workflow Triggers

- **Push** to `master`, `lab02`, `lab03`
- **Pull request** to `master`, `lab02`, `lab03`
- **Path filter:** Only when `app_python/**` or `.github/workflows/python-ci.yml` changes

### Versioning Strategy

**CalVer (Calendar Versioning)** — Format `YYYY.MM.DD` (e.g. `2026.02.04`). Chosen because this is a service deployed continuously rather than a library with breaking- change semantics. CalVer gives clear, date-based versions without manual tagging.

---

## 2. Workflow Evidence

| Item | Link / Evidence |
|------|-----------------|
| Successful workflow run | [GitHub Actions](https://github.com/abdughafforzoda/DevOps-Core-Course/actions/workflows/python-ci.yml) |
| Tests passing locally | See terminal output below |
| Docker image on Docker Hub | [jambulancia/devops-info-service](https://hub.docker.com/r/jambulancia/devops-info-service) |
| Status badge | In `app_python/README.md` |

**Tests passing locally:**

```
============================= test session starts ==============================
platform linux -- Python 3.13.3, pytest-9.0.2
collected 13 items

tests/test_app.py::test_index_returns_200 PASSED
tests/test_app.py::test_index_returns_json PASSED
tests/test_app.py::test_index_service_structure PASSED
tests/test_app.py::test_index_system_structure PASSED
tests/test_app.py::test_index_runtime_structure PASSED
tests/test_app.py::test_index_request_structure PASSED
tests/test_app.py::test_index_endpoints_list PASSED
tests/test_app.py::test_health_returns_200 PASSED
tests/test_app.py::test_health_returns_json PASSED
tests/test_app.py::test_health_structure PASSED
tests/test_app.py::test_404_nonexistent_endpoint PASSED
tests/test_app.py::test_404_wrong_method PASSED
tests/test_app.py::test_index_request_has_client_ip PASSED

============================== 13 passed in 0.06s ==============================
```

---

## 3. Best Practices Implemented

- **Dependency caching** — `actions/setup-python` with `cache: 'pip'` caches pip packages; speeds up jobs by ~30–60s on cache hit.
- **Concurrency** — `concurrency` cancels outdated workflow runs when new commits are pushed.
- **Path filters** — CI runs only when Python app files change, reducing unnecessary runs.
- **Job dependencies** — Docker job runs only after tests pass (`needs: test`).
- **Conditional Docker push** — Images pushed only on `push` (not on `pull_request`).
- **Snyk** — Vulnerability scan with `continue-on-error: true` so missing `SNYK_TOKEN` does not fail CI. Add `SNYK_TOKEN` for full scanning.
- **Docker layer caching** — `cache-from/cache-to: type=gha` reuses build layers between runs.

---

## 4. Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Versioning** | CalVer | Continuous deployment; date-based releases without manual version bumps. |
| **Docker tags** | `YYYY.MM.DD` + `latest` | E.g. `jambulancia/devops-info-service:2026.02.04` and `:latest`. |
| **Triggers** | Push + PR to master, lab02, lab03 | Validate changes before and after merge; runs on relevant branches. |
| **Test coverage** | All endpoints, structure, types | Ensures JSON shape and required fields; omits 500 handler due to needing forced failure. |
| **Linter** | Ruff | Fast, modern linter with good defaults. |

---

## 6. Bonus: Multi-App CI with Path Filters

A separate **Go CI** workflow (`.github/workflows/go-ci.yml`) runs when `app_go/**` changes. Both workflows use path filters so that:

- Changes to `app_python/` → only Python CI runs
- Changes to `app_go/` → only Go CI runs
- Changes to both → both run in parallel
- Changes to `docs/` or `labs/` → neither runs

**Benefits:** Fewer unnecessary runs, faster feedback, and lower Actions usage.

---

## 7. Setup Required

Before the workflow runs correctly:

1. **Docker Hub** — Add secrets in GitHub: `Settings → Secrets and variables → Actions`:
   - `DOCKERHUB_USERNAME`: your Docker Hub username
   - `DOCKERHUB_TOKEN`: Docker Hub access token (create at hub.docker.com)

2. **Snyk (optional)** — For security scanning:
   - Create account at snyk.io
   - Add `SNYK_TOKEN` as a GitHub secret
   - Without it, the Snyk step is skipped (`continue-on-error: true`)
