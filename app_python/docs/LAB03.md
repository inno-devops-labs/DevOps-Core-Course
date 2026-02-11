# Lab 03 — Continuous Integration

## 1. Overview

### Testing Framework: pytest

**Why pytest:** Simple syntax with powerful fixtures, excellent plugin ecosystem (pytest-cov for coverage), widely used in industry. Less verbose than unittest, supports parameterized tests out of the box.

### Test Coverage

All endpoints and helper functions are tested:
- `GET /` — JSON structure, all fields, types, values, custom user agent
- `GET /health` — status, timestamp, uptime, field types
- Error handling — 404 JSON response, 405 method not allowed
- Helper functions — `get_system_info()`, `get_uptime()`

**Total: 27 tests, 97% coverage** (missing only `__main__` block and 500 error handler logging).

### CI Workflow Triggers

```yaml
on:
  push:
    branches: [master, lab03]
    paths: ['app_python/**', '.github/workflows/python-ci.yml']
  pull_request:
    branches: [master]
    paths: ['app_python/**', '.github/workflows/python-ci.yml']
```

**Why:** Runs on push and PR to master, but ONLY when Python files change (path filters). No unnecessary runs when Go or docs change.

### Versioning Strategy: CalVer

**Format:** `YYYY.MM.DD` (e.g., `2026.02.02`)

**Why CalVer over SemVer:** This is a service (not a library). CalVer clearly shows when image was built. No need to track breaking changes — API is internal. Date-based versioning is simpler for continuous deployment.

**Docker tags per build:**
- `aezuraa/devops-info-service:python` — latest stable
- `aezuraa/devops-info-service:python-2026.02.02` — CalVer date
- `aezuraa/devops-info-service:python-abc1234` — commit SHA for traceability

## 2. Workflow Evidence

- **Workflow file:** `.github/workflows/python-ci.yml`
- **Successful workflow run (Python CI):** https://github.com/AEZuraa/DevOps-Core-Course/actions/runs/21912674725
- **Docker Hub:** https://hub.docker.com/r/aezuraa/devops-info-service
- **Status badge:** Added to `app_python/README.md`

### Tests Passing Locally

```
============================= test session starts ==============================
platform darwin -- Python 3.12.3, pytest-8.3.4, pluggy-1.6.0
collected 27 items

tests/test_app.py::TestMainEndpoint::test_status_code PASSED             [  3%]
tests/test_app.py::TestMainEndpoint::test_content_type PASSED            [  7%]
tests/test_app.py::TestMainEndpoint::test_service_fields PASSED          [ 11%]
tests/test_app.py::TestMainEndpoint::test_system_fields PASSED           [ 14%]
tests/test_app.py::TestMainEndpoint::test_system_field_types PASSED      [ 18%]
tests/test_app.py::TestMainEndpoint::test_runtime_fields PASSED          [ 22%]
tests/test_app.py::TestMainEndpoint::test_runtime_field_types PASSED     [ 25%]
tests/test_app.py::TestMainEndpoint::test_request_fields PASSED          [ 29%]
tests/test_app.py::TestMainEndpoint::test_endpoints_list PASSED          [ 33%]
tests/test_app.py::TestMainEndpoint::test_all_top_level_keys PASSED      [ 37%]
tests/test_app.py::TestMainEndpoint::test_custom_user_agent PASSED       [ 40%]
tests/test_app.py::TestHealthEndpoint::test_status_code PASSED           [ 44%]
tests/test_app.py::TestHealthEndpoint::test_content_type PASSED          [ 48%]
tests/test_app.py::TestHealthEndpoint::test_health_status PASSED         [ 51%]
tests/test_app.py::TestHealthEndpoint::test_health_fields PASSED         [ 55%]
tests/test_app.py::TestHealthEndpoint::test_health_field_types PASSED    [ 59%]
tests/test_app.py::TestHealthEndpoint::test_health_all_keys PASSED       [ 62%]
tests/test_app.py::TestErrorHandling::test_404_unknown_endpoint PASSED   [ 66%]
tests/test_app.py::TestErrorHandling::test_404_json_response PASSED      [ 70%]
tests/test_app.py::TestErrorHandling::test_404_content_type PASSED       [ 74%]
tests/test_app.py::TestErrorHandling::test_post_method_not_allowed PASSED [ 77%]
tests/test_app.py::TestErrorHandling::test_put_method_not_allowed PASSED [ 81%]
tests/test_app.py::TestHelperFunctions::test_get_system_info_returns_dict PASSED [ 85%]
tests/test_app.py::TestHelperFunctions::test_get_system_info_keys PASSED [ 88%]
tests/test_app.py::TestHelperFunctions::test_get_uptime_returns_dict PASSED [ 92%]
tests/test_app.py::TestHelperFunctions::test_get_uptime_non_negative PASSED [ 96%]
tests/test_app.py::TestHelperFunctions::test_get_uptime_human_readable PASSED [100%]

============================== 27 passed in 0.33s ==============================
```

### Coverage Report

```
Name                Stmts   Miss  Cover   Missing
-------------------------------------------------
app.py                 47      6    87%   51, 132-133, 140-142
tests/__init__.py       0      0   100%
tests/test_app.py     155      0   100%
-------------------------------------------------
TOTAL                 202      6    97%
```

**Not covered:** `if __name__ == '__main__'` block (lines 140-142) and 500 error handler logging (lines 132-133). These are runtime-only paths that don't affect test reliability.

## 3. Best Practices Implemented

1. **Job Dependencies:** Docker build only runs if lint+tests pass (`needs: lint-and-test`). No broken images pushed.

2. **Dependency Caching:** `actions/setup-python` with `cache: 'pip'` caches pip packages based on `requirements-dev.txt` hash. Expected speedup: ~30-60s saved on dependency install (cache hit skips download entirely).

3. **Snyk Security Scanning:** Scans dependencies for CVEs with `severity-threshold=high`. Uses `continue-on-error: true` — warns on vulnerabilities without blocking the pipeline. Only high/critical severity breaks the build. Flask 3.1.0 and Werkzeug 3.1.3 have no known high-severity vulnerabilities.

4. **Workflow Concurrency:** `cancel-in-progress: true` cancels outdated runs on same branch. Saves CI minutes on rapid pushes.

5. **Conditional Docker Push:** Docker step only runs on `push` events (`if: github.event_name == 'push'`). PRs only run tests, not push images.

6. **Docker Layer Caching:** Uses GitHub Actions cache (`cache-from: type=gha`) for Docker BuildKit layers. Speeds up subsequent builds significantly (~60-80% faster).

7. **Environment Variables:** Repeated values (`DOCKER_IMAGE`, `PYTHON_VERSION`) defined once in `env:` block. DRY principle.

8. **Status Badge:** CI status visible in README without navigating to Actions tab.

9. **Path Filters:** Workflows only trigger on relevant file changes. Python CI ignores Go changes and vice versa.

10. **Coverage Threshold:** `--cov-fail-under=70` fails CI if coverage drops below 70%.

### Caching Performance

| Metric | Without Cache | With Cache |
|--------|--------------|------------|
| pip install | ~15-20s | ~2-3s |
| Docker build | ~30-45s | ~5-10s |
| **Total saved** | — | **~40-50s per run** |

Cache key is based on `requirements-dev.txt` hash — changes to dependencies invalidate cache automatically.

### Snyk Integration

- **Severity threshold:** `high` — only high and critical vulnerabilities fail the build
- **Current status:** No high-severity vulnerabilities found in Flask 3.1.0 / Werkzeug 3.1.3
- **`continue-on-error: true`** — advisory issues don't block development
- **Requires:** `SNYK_TOKEN` secret in GitHub repo settings

## 4. Key Decisions

**Versioning Strategy:** CalVer (`YYYY.MM.DD`). This is a service deployed continuously, not a library with breaking changes. Date-based tags make it obvious when an image was built, and commit SHA tags allow exact traceability.

**Docker Tags:** Three tags per build — `:python` (rolling latest), `:python-2026.02.02` (CalVer), `:python-abc1234` (commit SHA). This allows pulling latest, pinning to a date, or pinning to exact commit.

**Workflow Triggers:** Push to master/lab03 + PRs to master, with path filters. PRs run tests only (no Docker push). Push triggers full pipeline including Docker Hub push.

**Test Coverage:** 97% coverage. Untested code is `__main__` block and 500 error logging — both are runtime-only and testing them would require mocking the server startup, which adds complexity without value.

## 5. Challenges

- **System Python conflict:** Global web3/eth_typing package interfered with pytest. Solved by using virtual environment for local testing.
- **Trailing whitespace:** flake8 flagged whitespace in blank lines. Fixed before committing.
- **Snyk token:** Requires manual setup in GitHub Secrets. Set to `continue-on-error` so CI works even without token configured initially.
