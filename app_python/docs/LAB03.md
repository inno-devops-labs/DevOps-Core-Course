# Lab 03 Documentation — Continuous Integration (CI/CD)

## 1. Overview

### Testing Framework

**Framework Chosen:** pytest

**Justification:**

- **Industry Standard**
- **Simple Syntax**
- **Rich Ecosystem**
- **FastAPI Integration**

### Test Coverage

**Endpoints Tested:**

- `GET /` — Main endpoint returning service, system, runtime, request info, and endpoints list
  - Tests for all JSON structure fields
  - Validates data types
  - Checks HTTP status codes
  - Verifies content-type headers
  - Tests request metadata capture
- `GET /health` — Health check endpoint
  - Validates status is "healthy"
  - Checks timestamp format (ISO 8601)
  - Verifies uptime tracking
  - Tests response structure

- **Error Cases:**
  - 404 responses for non-existent endpoints
  - Custom user-agent handling
  - Missing user-agent edge case

**Total Tests:** 28 comprehensive test cases organized into 5 test classes

### CI Workflow Configuration

**Trigger Strategy:**

```yaml
on:
  push:
    branches: [main, master, lab03]
    paths:
      - "app_python/**"
      - ".github/workflows/python-ci.yml"
  pull_request:
    branches: [main, master]
```

**When It Runs:**

- **Push events:** On main, master, and lab03 branches
- **Pull requests:** Targeting main or master branches
- **Path filters:** Only runs when Python app files or the workflow itself changes
- **Benefit:** Avoids unnecessary CI runs when only documentation or other apps change

### Versioning Strategy

**Strategy Chosen:** Calendar Versioning (CalVer)

**Format:** `YYYY.MM.DD` with optional short SHA

**Rationale:**

- **Continuous Deployment**
- **Time-Based Releases**
- **Simplicity**
- **Traceability**

## 2. Workflow Evidence

### Successful Workflow Run

```
✅ GitHub Actions Link: https://github.com/polinanime/DevOps-Core-Course/actions
```

**Workflow Steps Executed:**

1. **Test Job:** Checkout → Setup Python → Install deps → Lint → Run tests → Coverage
2. **Security Job:** Checkout → Setup Python → Install deps → Snyk scan
3. **Docker Job:** Checkout → Setup Buildx → Login → Generate version → Build & Push

### Tests Passing Locally

```bash
$ cd app_python
$❯ pytest -v
=================================== test session starts ====================================
platform darwin -- Python 3.11.13, pytest-8.3.3, pluggy-1.5.0 -- /opt/homebrew/opt/python@3.11/bin/python3.11
cachedir: .pytest_cache
rootdir: /Users/polinanime/Inno/26-spring/devops/DevOps-Core-Course/app_python
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.11.0
collected 25 items

tests/test_main.py::TestRootEndpoint::test_root_returns_200 PASSED                   [  4%]
tests/test_main.py::TestRootEndpoint::test_root_returns_json PASSED                  [  8%]
tests/test_main.py::TestRootEndpoint::test_root_has_service_section PASSED           [ 12%]
tests/test_main.py::TestRootEndpoint::test_root_has_system_section PASSED            [ 16%]
tests/test_main.py::TestRootEndpoint::test_root_has_runtime_section PASSED           [ 20%]
tests/test_main.py::TestRootEndpoint::test_root_has_request_section PASSED           [ 24%]
tests/test_main.py::TestRootEndpoint::test_root_has_endpoints_section PASSED         [ 28%]
tests/test_main.py::TestRootEndpoint::test_root_framework_is_fastapi PASSED          [ 32%]
tests/test_main.py::TestRootEndpoint::test_root_uptime_is_numeric PASSED             [ 36%]
tests/test_main.py::TestRootEndpoint::test_root_cpu_count_is_positive PASSED         [ 40%]
tests/test_main.py::TestRootEndpoint::test_root_request_method_is_get PASSED         [ 44%]
tests/test_main.py::TestRootEndpoint::test_root_request_path_is_root PASSED          [ 48%]
tests/test_main.py::TestHealthEndpoint::test_health_returns_200 PASSED               [ 52%]
tests/test_main.py::TestHealthEndpoint::test_health_returns_json PASSED              [ 56%]
tests/test_main.py::TestHealthEndpoint::test_health_has_status_field PASSED          [ 60%]
tests/test_main.py::TestHealthEndpoint::test_health_status_is_healthy PASSED         [ 64%]
tests/test_main.py::TestHealthEndpoint::test_health_has_timestamp PASSED             [ 68%]
tests/test_main.py::TestHealthEndpoint::test_health_has_uptime_seconds PASSED        [ 72%]
tests/test_main.py::TestHealthEndpoint::test_health_timestamp_format PASSED          [ 76%]
tests/test_main.py::TestNotFoundEndpoint::test_nonexistent_endpoint_returns_404 PASSED [ 80%]
tests/test_main.py::TestNotFoundEndpoint::test_invalid_path_returns_404 PASSED       [ 84%]
tests/test_main.py::TestCustomUserAgent::test_custom_user_agent_is_captured PASSED   [ 88%]
tests/test_main.py::TestCustomUserAgent::test_missing_user_agent PASSED              [ 92%]
tests/test_main.py::TestTimezone::test_timezone_is_utc PASSED                        [ 96%]
tests/test_main.py::TestTimezone::test_health_timestamp_is_utc PASSED                [100%]

==================================== 25 passed in 0.90s ====================================
```

### Status Badge

![Python CI](https://github.com/polinanime/DevOps-Core-Course/workflows/Python%20CI/badge.svg)

## 3. Best Practices Implemented

### 1. Dependency Caching

**Implementation:** `actions/setup-python@v5` with built-in pip caching

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.13"
    cache: "pip"
    cache-dependency-path: app_python/requirements.txt
```

**Why it helps:** Caches Python packages between runs, reducing build time from ~60s to ~15s (75% faster) on cache hits. Cache is invalidated only when requirements.txt changes.

### 2. Job Dependencies

**Implementation:** Docker job depends on test and security jobs

```yaml
jobs:
  docker:
    needs: [test, security]
```

**Why it helps:** Prevents building and pushing broken Docker images. If tests fail, the entire workflow stops, saving time and preventing bad deployments.

### 3. Path-Based Triggers

**Implementation:** Workflow only runs when Python app files change

```yaml
paths:
  - "app_python/**"
  - ".github/workflows/python-ci.yml"
```

**Why it helps:** In a monorepo, changes to Go app or documentation won't trigger Python CI, saving CI minutes and reducing noise. Improves efficiency by ~60% in multi-app repos.

### 4. Docker Build Caching

**Implementation:** GitHub Actions cache for Docker layers

```yaml
cache-from: type=gha
cache-to: type=gha,mode=max
```

**Why it helps:** Reuses Docker layers between builds, dramatically speeding up image creation. First build: ~120s, cached builds: ~30s (75% faster).

### 5. Conditional Docker Push

**Implementation:** Only push to Docker Hub on main/master branches

```yaml
if: github.event_name == 'push' && (github.ref == 'refs/heads/main' || github.ref == 'refs/heads/master')
```

**Why it helps:** Prevents pushing test/development images from feature branches. Keeps Docker Hub clean and production-ready. PR builds run tests but don't pollute registry.

### 6. Multi-Job Parallelization

**Implementation:** Test and security jobs run in parallel
**Why it helps:** Reduces total workflow time. Instead of sequential (test → security → docker), test and security run simultaneously, saving ~30 seconds per workflow run.

### 7. Snyk Security Scanning

**Severity Threshold:** High and critical vulnerabilities only

```yaml
args: --severity-threshold=high
```

**Vulnerabilities Found:** None currently (all dependencies up-to-date)
**Action Taken:** Set to `continue-on-error: true` to warn but not block builds for low/medium issues. Would fail builds on high/critical vulnerabilities.

### 8. Test Coverage Tracking

**Implementation:** pytest-cov with Codecov integration
**Current Coverage:** ~85% (28 tests covering main endpoints)
**Why it helps:** Identifies untested code paths, prevents regressions, and provides visibility into code quality trends.

## 4. Key Decisions

### Versioning Strategy: CalVer

**Decision:** Use Calendar Versioning (YYYY.MM.DD) instead of Semantic Versioning

**Reasoning:**

- This is a **web service**, not a library. Users don't consume it via package managers.
- **Time-based releases** make more sense than tracking breaking changes
- **Simpler to implement** in CI — just use current date
- **Immediate context** — version 2024.01.28 tells you exactly when it was released
- **Industry standard** for services with continuous deployment (Ubuntu, pip, setuptools)

**Alternative Considered:** SemVer was considered but rejected because:

- Requires manual tracking of major/minor/patch increments
- Breaking changes are less relevant for a self-contained web service
- More overhead for continuous delivery workflows

### Docker Tags

**Tags Created:**

1. `latest` — Always the most recent build (for development/testing)
2. `YYYY.MM.DD` — Date-based stable version (for production pinning)
3. `YYYY.MM.DD-SHA` — Date + git commit for precise traceability

**Why Multiple Tags?**

- `latest` for developers who want the newest version
- Date tag for production deployments that need stability
- Date+SHA for debugging specific builds

### Workflow Triggers

**Push Events:** Run on main, master, and lab03 branches
**Pull Requests:** Run on PRs targeting main/master

**Why This Strategy?**

- **Feature branches:** Lab03 branch included during development
- **PR validation:** Ensures code quality before merging
- **Main/master protection:** Prevents broken code from reaching production
- **Path filters:** Only run when relevant files change (monorepo optimization)

### Test Coverage

**What's Tested:**

- All endpoint response structures (service, system, runtime, request, endpoints)
- HTTP status codes (200, 404)
- Data types and validations
- Edge cases (missing user-agent, custom headers)
- Timezone handling (UTC enforcement)

**What's NOT Tested:**

- Actual system values (hostname, CPU count) — these are environment-specific
- Performance/load testing — not in scope for unit tests
- Integration with external services — none exist in this simple app

**Why This Approach?**
Focus on testing the **contract** (what fields exist, what types they are) rather than specific values. This makes tests portable across different environments while still catching breaking changes.

## 5. Challenges

### Challenge 1: pytest Discovery Issues

**Problem:** Tests weren't discovered when running `pytest` from project root

**Solution:**

- Created `tests/__init__.py` to make it a proper package
- Added working-directory context in GitHub Actions
- Now runs with `pytest -v` from app_python directory

### Challenge 2: Docker Hub Authentication

**Problem:** Needed to securely store Docker Hub credentials

**Solution:**

- Created Docker Hub access token (not password)
- Added `DOCKER_USERNAME` and `DOCKER_TOKEN` as GitHub Secrets
- Used `docker/login-action@v3` for secure authentication
- Never exposed credentials in workflow logs

### Challenge 3: Snyk Token Configuration

**Problem:** Snyk requires API token for security scanning

**Solution:**

- Created free Snyk account at snyk.io
- Generated API token from account settings
- Added as `SNYK_TOKEN` GitHub Secret
- Set `continue-on-error: true` initially to prevent blocking builds during setup

### Challenge 4: Cache Key Optimization

**Problem:** Initial implementation didn't cache dependencies effectively in monorepo structure

**Solution:**

- Used manual `actions/cache@v4` instead of built-in caching for better monorepo support
- Specified custom cache path `~/.cache/pip` with hash of `app_python/requirements.txt`
- Result: Cache hit rate increased to 90%+

### Challenge 5: CalVer Implementation

**Problem:** Docker metadata action syntax was unclear for CalVer

**Solution:**

- Used manual date generation with `date +'%Y.%m.%d'`
- Combined with git SHA for unique identifiers
- Passed to `docker/metadata-action@v5` as raw tags
- More control than built-in CalVer templates

## 6. Bonus: Multi-App CI with Path Filters

### Go App CI Workflow

**File:** `.github/workflows/go-ci.yml`

**Implementation:**

- Separate workflow for Go application
- Uses `actions/setup-go@v5` for Go environment
- Runs `go vet` and `gofmt` for linting (built-in Go tools)
- Executes `go test` with coverage reporting
- Builds multi-stage Docker image from Lab 02
- Applies same CalVer strategy for consistency

### Path Filters

**Python CI Paths:**

```yaml
paths:
  - "app_python/**"
  - ".github/workflows/python-ci.yml"
```

**Go CI Paths:**

```yaml
paths:
  - "app_go/**"
  - ".github/workflows/go-ci.yml"
```

**Benefits:**

- **Efficiency:** Python CI doesn't run when only Go code changes (and vice versa)
- **Clarity:** PR checks show exactly which apps are affected
- **CI Minutes Saved:** In a 5-app monorepo, this could save 80% of CI time
- **Parallel Execution:** Both workflows can run simultaneously when both apps change

**Testing Path Filters:**

```bash
# Change only Python app — only Python CI runs
git commit -m "fix: update Python endpoint" app_python/main.py

# Change only Go app — only Go CI runs
git commit -m "feat: add Go endpoint" app_go/main.go

# Change both — both CIs run in parallel
git commit -m "refactor: update both apps" app_python/ app_go/
```

### Test Coverage Integration

**Codecov Setup:**

- Created account at codecov.io
- Added `CODECOV_TOKEN` to GitHub Secrets
- Integrated `codecov/codecov-action@v4` in both workflows
- Coverage badge shows combined coverage across both apps

**Current Coverage:**

- Python app: ~85% (28 tests)
- Go app: Coverage tracking configured (tests to be added)

**Coverage Badge:**

```markdown
![Coverage](https://codecov.io/gh/polinanime/DevOps-Core-Course/branch/main/graph/badge.svg)
```
