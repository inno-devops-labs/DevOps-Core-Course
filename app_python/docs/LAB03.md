# Lab 03 — Continuous Integration (CI/CD)

## 1. Overview

### Testing Framework: pytest

Chose **pytest** over unittest because:

- Concise syntax — no boilerplate class inheritance or `self.assert*` methods required
- Powerful fixtures (`@pytest.fixture`) for clean test setup
- Rich plugin ecosystem — `pytest-cov` for coverage, `flake8` for linting
- Better test discovery and output formatting
- De facto standard for modern Python projects

### Test Coverage

Tests cover all application endpoints:

| Endpoint | Tests |
|----------|-------|
| `GET /` | Status code, content type, all JSON sections (service, system, runtime, request, endpoints), custom User-Agent forwarding |
| `GET /health` | Status code, content type, status field, timestamp, uptime |
| 404 handler | Unknown routes return 404 JSON, correct path in error response, multiple paths |

**16 tests total**, 89% coverage on `app.py` (only `if __name__` block and 500 handler body uncovered).

### CI Workflow Triggers

Both workflows trigger on:
- **Push** to `master` or `lab03` branches
- **Pull requests** targeting `master`
- **Path filters** — only when relevant app files change

### Versioning Strategy: CalVer

Chose **Calendar Versioning** (`YYYY.MM.RUN_NUMBER`) because:
- This is a continuously deployed service, not a library with semver-style breaking changes
- Date-based tags clearly communicate when a build was produced
- Combined with GitHub Actions `run_number` to ensure uniqueness within a month

## 2. Workflow Evidence

- Successful workflow run: check the [Actions tab](https://github.com/merkulovleo/DevOps-Core-Course/actions)
- Docker Hub image: [merkulovlr05/devops-info](https://hub.docker.com/r/merkulovlr05/devops-info)
- Status badge visible in [app_python/README.md](../README.md)

### Tests passing locally

```
tests/test_app.py::TestIndexEndpoint::test_index_status_code PASSED
tests/test_app.py::TestIndexEndpoint::test_index_content_type PASSED
tests/test_app.py::TestIndexEndpoint::test_index_has_service_section PASSED
tests/test_app.py::TestIndexEndpoint::test_index_has_system_section PASSED
tests/test_app.py::TestIndexEndpoint::test_index_has_runtime_section PASSED
tests/test_app.py::TestIndexEndpoint::test_index_has_request_section PASSED
tests/test_app.py::TestIndexEndpoint::test_index_has_endpoints_section PASSED
tests/test_app.py::TestIndexEndpoint::test_index_user_agent_forwarded PASSED
tests/test_app.py::TestHealthEndpoint::test_health_status_code PASSED
tests/test_app.py::TestHealthEndpoint::test_health_content_type PASSED
tests/test_app.py::TestHealthEndpoint::test_health_status_field PASSED
tests/test_app.py::TestHealthEndpoint::test_health_has_timestamp PASSED
tests/test_app.py::TestHealthEndpoint::test_health_has_uptime PASSED
tests/test_app.py::TestErrorHandlers::test_404_for_unknown_route PASSED
tests/test_app.py::TestErrorHandlers::test_404_json_content_type PASSED
tests/test_app.py::TestErrorHandlers::test_404_different_paths PASSED

16 passed in 0.15s
```

## 3. Best Practices Implemented

| Practice | Why it helps |
|----------|-------------|
| **Dependency caching** | `actions/setup-python` with `cache: pip` reuses downloaded packages — cuts install time from ~15s to ~2s on cache hit |
| **Concurrency control** | `cancel-in-progress: true` cancels outdated runs on the same branch, saving CI minutes |
| **Job dependencies** | Docker build (`needs: test`) only runs if lint+tests pass — no broken images pushed |
| **Path-based triggers** | Python CI only fires on `app_python/**` changes, Go CI on `app_go/**` — avoids wasted runs |
| **Docker layer caching** | `cache-from/to: type=gha` with Buildx reuses Docker build layers across runs |
| **Snyk security scan** | Checks dependencies for known CVEs; set to `continue-on-error: true` so advisory vulnerabilities don't block deploys, but high-severity issues are flagged |
| **Status badge** | Visible CI health indicator in README |

## 4. Key Decisions

**Versioning Strategy:** CalVer (`YYYY.MM.RUN_NUMBER`). A web service with continuous deployment benefits more from time-based versions than semantic versioning — there are no "breaking changes" for downstream consumers.

**Docker Tags:** Each push produces two tags — a CalVer tag (e.g., `2026.02.5`) for traceability and `latest` for convenience. This allows rollback to any specific build while keeping `latest` as a simple default.

**Workflow Triggers:** Push to `master`/`lab03` + PRs to `master`. This ensures CI validates every change before merge while also building images on push. Path filters prevent unnecessary runs.

**Test Coverage:** 89% on app.py. The 4 uncovered lines are the `if __name__ == "__main__"` entry point and the 500 error handler body — both are runtime/integration concerns that don't need unit testing.

## 5. Bonus

### Multi-App CI with Path Filters

Created separate workflows for Python (`python-ci.yml`) and Go (`go-ci.yml`). Each uses `paths:` filters so changes to one app don't trigger the other's pipeline. Both workflows can run in parallel since they are independent jobs.

Benefits of path-based triggers in a monorepo:
- Faster feedback — only relevant tests run
- Reduced CI costs — no wasted compute on unchanged code
- Clearer signal — a green check means the changed app is healthy

### Test Coverage Tracking

- Python: `pytest-cov` generates XML coverage reports, uploaded to Codecov via `codecov/codecov-action@v4`
- Go: `go test -coverprofile` generates coverage data, also uploaded to Codecov
- Coverage flags (`python`, `go`) keep reports separate in the Codecov dashboard
