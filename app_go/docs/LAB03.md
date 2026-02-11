# Lab 3 Bonus — Multi-App CI with Path Filters + Test Coverage

## Part 1: Multi-App CI

### 1.1 Second CI Workflow: Go

**File:** `.github/workflows/go-ci.yml`

**Implementation:**
- **Linter:** golangci-lint (standard for Go)
- **Tests:** `go test -v -race -coverprofile=coverage.out`
- **Docker:** Build & push with CalVer (same strategy as Python)
- **Actions:** `actions/setup-go@v5`, `golangci/golangci-lint-action@v6`, `docker/build-push-action@v6`

**Versioning:** CalVer (`YYYY.MM.BUILD`) aligned with Python workflow.

**Docker image:** `mirana18/devops-info-service-go`

### 1.2 Path-Based Triggers

| Workflow     | Triggers on changes to                                   |
|-------------|----------------------------------------------------------|
| Python CI   | `app_python/**`, `.github/workflows/python-ci.yml`       |
| Go CI       | `app_go/**`, `.github/workflows/go-ci.yml`               |

**No workflow runs** when only these change:
- `docs/`, `labs/`, `lectures/`
- `README.md`, `.gitignore`
- Root-level or other non-app files

**Selective triggering:**
- Change only `app_python/app.py` → Python CI runs, Go CI does not
- Change only `app_go/main.go` → Go CI runs, Python CI does not
- Change `app_python/` and `app_go/` in one commit → both run in parallel

### 1.3 Benefits of Path Filters

| Benefit             | Description                                                                 |
|---------------------|-----------------------------------------------------------------------------|
| **Faster feedback** | Only relevant workflows run → shorter queue and quicker results             |
| **Cost savings**    | Fewer GitHub Actions minutes spent on unrelated changes                     |
| **Parallel runs**   | Python and Go pipelines are independent and can run at the same time        |
| **Clear ownership** | Each app has its own pipeline                                               |
| **Doc-safe**        | Updates to docs/labs do not trigger builds or Docker pushes                 |

### 1.4 Proof of Selective Triggering

**Scenario 1: Only Python changes**

```
Modified files: app_python/app.py
→ Python CI: runs
→ Go CI: skipped (no matching paths)
```

**Scenario 2: Only Go changes**

```
Modified files: app_go/main.go
→ Python CI: skipped
→ Go CI: runs
```

**Scenario 3: Both apps changed**

```
Modified files: app_python/app.py, app_go/main.go
→ Python CI: runs
→ Go CI: runs (in parallel)
```

---

## Part 2: Test Coverage 

### 2.1 Coverage Tools

| App    | Tool          | Command                                              | Output              |
|--------|---------------|------------------------------------------------------|---------------------|
| Python | pytest-cov    | `pytest --cov=. --cov-report=xml --cov-fail-under=70` | `coverage.xml`      |
| Go     | go test       | `go test -coverprofile=coverage.out ./...`           | `coverage.out`      |

### 2.2 Codecov Integration

- **Service:** codecov.io
- **Action:** `codecov/codecov-action@v4`
- **Flags:** `python` and `go` for separate reporting
- **Token:** Optional `CODECOV_TOKEN` in GitHub Secrets (works for public repos without it, with `fail_ci_if_error: false`)

### 2.3 Coverage Badges

Added to README files:

- **app_python/README.md:** Python CI badge + Codecov (python flag)
- **app_go/README.md:** Go CI badge + Codecov (go flag)

**Badge URLs:**
```
https://github.com/Arino4kaMyr/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg
https://github.com/Arino4kaMyr/DevOps-Core-Course/actions/workflows/go-ci.yml/badge.svg
https://codecov.io/gh/Arino4kaMyr/DevOps-Core-Course/graph/badge.svg?flag=python
https://codecov.io/gh/Arino4kaMyr/DevOps-Core-Course/graph/badge.svg?flag=go
```

### 2.4 Coverage Analysis

#### Python

| Metric        | Value        |
|---------------|--------------|
| Threshold     | 70% (`--cov-fail-under=70`) |
| Covered       | Endpoints (`/`, `/health`), helpers, error handling, integration tests |
| Not covered   | `if __name__ == '__main__'` block, some internal error handlers |

**What’s tested:**
- `GET /` — JSON structure, required fields, types
- `GET /health` — status, timestamp, uptime
- 404, 405 responses
- `format_uptime()`, `get_system_info()`
- Basic integration scenarios

**Deliberately not covered:**
- Main entry point (`main` block)
- Rare error paths that are hard to trigger in tests

#### Go

| Metric        | Value        |
|---------------|--------------|
| Approx. coverage | ~85% (from `go test -coverprofile`) |
| Covered       | mainHandler, healthHandler, formatUptime, getClientIP |
| Not covered   | `main()` (server startup), error branches in getHostname |

**What’s tested:**
- `mainHandler` — service/system/runtime/request/endpoints
- `healthHandler` — status, timestamp, uptime
- `formatUptime` — 0s, 1s, 65s, 3661s, 7200s
- `getClientIP` — X-Forwarded-For, X-Real-Ip

### 2.5 Coverage Threshold in CI

**Python:** CI fails if coverage drops below 70%.

```yaml
pytest --cov=. --cov-report=xml --cov-fail-under=70
```

**Go:** No explicit threshold yet; coverage is collected and sent to Codecov for reporting.

---

## Summary

| Requirement                         | Status |
|-------------------------------------|--------|
| Second workflow for Go              | ✅ `go-ci.yml` |
| Path filters for Python             | ✅ `app_python/**` |
| Path filters for Go                 | ✅ `app_go/**` |
| Both workflows run in parallel      | ✅ Independent triggers |
| Coverage tool (pytest-cov, go test) | ✅ |
| Coverage reports in CI              | ✅ |
| Codecov integration                 | ✅ |
| Coverage badges in README           | ✅ |
| Coverage threshold (Python ≥70%)    | ✅ |
| Documentation of coverage           | ✅ |
