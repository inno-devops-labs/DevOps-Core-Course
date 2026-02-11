# Lab 3 — Go CI/CD (Bonus Task)

## 1. Overview

### Go CI Workflow

**Workflow File:** `.github/workflows/go-ci.yml`  
**Purpose:** Automated testing, linting, security scanning, and Docker image publishing for the Go application.

**Workflow Triggers:**
- **Push Events:** Runs on pushes to `main`, `master`, and `lab3` branches
- **Pull Requests:** Runs on PRs targeting `main` or `master`
- **Path Filters:** Only triggers when Go app files or workflow itself changes

```yaml
on:
  push:
    branches: [ main, master, lab3 ]
    paths:
      - 'app_go/**'
      - '.github/workflows/go-ci.yml'
  pull_request:
    branches: [ main, master ]
    paths:
      - 'app_go/**'
      - '.github/workflows/go-ci.yml'
```

**Rationale:**
- Python CI does not run when only Go code changes
- Go CI does not run when only Python code changes
- Saves CI minutes and gives faster, relevant feedback

### Versioning Strategy

**Strategy:** Calendar Versioning (CalVer), same as Python app (consistent across monorepo).

**Docker Tags Generated:**
- `latest` (only on main/master branch)
- `YYYY.MM.DD` (date-based version, e.g. `2026.02.11`)

**Implementation:** Uses `docker/metadata-action@v5`; same two-tag strategy as Python workflow.

### Language-Specific Setup

- **Go Version:** 1.22
- **Linter:** golangci-lint
- **Testing:** `go test` with race detector (`-race`) and coverage (`-coverprofile=coverage.out`)
- **Security:** Snyk for Go dependencies
- **Coverage:** Codecov (upload `coverage.out`)

---

## 2. Workflow Evidence

### Go Workflow Structure

**Jobs:**
1. **Test Job:**
   - Checkout code
   - Set up Go 1.22 (with cache on `app_go/go.sum`)
   - `go mod download` and `go mod verify`
   - Lint with golangci-lint
   - Run tests: `go test -v -race -coverprofile=coverage.out ./...`
   - Generate HTML coverage: `go tool cover -html=coverage.out -o coverage.html`
   - Upload coverage to Codecov

2. **Security Job:** (depends on test)
   - Checkout code
   - Run Snyk for Go: `snyk/actions/golang@master` with `--severity-threshold=high`
   - `continue-on-error: true` (warning mode)

3. **Build-and-Push Job:** (depends on test, security; only on push)
   - Checkout, Docker Buildx, Docker Hub login
   - Extract metadata (tags)
   - Build and push Docker image with layer caching

**Workflow Link:** [GitHub Actions — Go CI/CD](https://github.com/karishka1222/DevOps-Core-Course/actions/workflows/go-ci.yml)

### Docker Hub Images (Go)

**Repository:** `https://hub.docker.com/repository/docker/karishka1222/devops-go-app`

**Tags Available:**
- `latest` — Latest build from main/master branch
- `YYYY.MM.DD` — Date-based version (e.g. `2026.02.11`)

**Pull Command:**
```bash
docker pull karishka1222/devops-go-app:latest
docker pull karishka1222/devops-go-app:2026.02.11
```

### Unit Tests (Go)

**Test File:** `app_go/main_test.go`

**Test Cases:**
- `TestMainEndpoint` — GET / (status, JSON structure, required fields)
- `TestHealthEndpoint` — GET /health (status, structure, healthy)
- `TestGetSystemInfo` — System info fields and types
- `TestGetUptime` — Uptime calculation and format
- `TestNotFoundHandler` — 404 response and JSON
- `TestConcurrentRequests` — Multiple concurrent GET /
- `TestUptimeIncreases` — Uptime increases over time
- `TestFormatUptime` — All branches of uptime formatting (seconds/minutes/hours, singular/plural)
- `TestGetSystemInfoHostnameError` — getSystemInfo when hostname fails (fallback to "unknown")
- `TestGetRequestInfo` — Request info extraction (X-Forwarded-For, empty User-Agent → "unknown")
- `TestMainHandlerWriteError` — mainHandler when JSON encode/write fails
- `TestHealthHandlerWriteError` — healthHandler when JSON encode/write fails
- `TestNotFoundHandlerWriteError` — notFoundHandler when JSON encode/write fails

**Run Tests Locally:**
```bash
cd app_go
go test -v -race -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

---

## 3. Best Practices Implemented

### 1. Path-Based Triggers

**Implementation:**
```yaml
on:
  push:
    paths:
      - 'app_go/**'
      - '.github/workflows/go-ci.yml'
```

**Why It Helps:**
- Go CI runs only when Go app or its workflow changes
- Reduces unnecessary runs when only Python or docs change
- Both Python and Go workflows can run in parallel when both apps change

### 2. Go Module Caching

**Implementation:**
```yaml
- name: Set up Go
  uses: actions/setup-go@v5
  with:
    go-version: '1.22'
    cache-dependency-path: app_go/go.sum
```

**Why It Helps:**
- Speeds up dependency installation
- Cache invalidates when `go.sum` changes

### 3. Job Dependencies (Fail Fast)

**Implementation:**
```yaml
security:
  needs: test

build-and-push:
  needs: [test, security]
  if: github.event_name == 'push'
```

**Why It Helps:**
- Docker image is built only if tests and security scan complete
- Prevents publishing images when tests fail

### 4. Docker Layer Caching

**Implementation:**
```yaml
cache-from: type=gha
cache-to: type=gha,mode=max
```

**Why It Helps:**
- Reuses Docker layers between runs
- Faster builds

### 5. Security Scanning (Snyk for Go)

**Implementation:**
```yaml
- name: Run Snyk to check for vulnerabilities
  uses: snyk/actions/golang@master
  continue-on-error: true
  with:
    args: --severity-threshold=high
    command: test
  env:
    SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
```

**Why It Helps:**
- Detects known vulnerabilities in Go dependencies
- Same approach as Python app (warning mode)

### 6. Test Coverage (Codecov)

**Implementation:**
```yaml
- name: Run tests
  run: go test -v -race -coverprofile=coverage.out ./...

- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v4
  with:
    file: ./app_go/coverage.out
    flags: go
    fail_ci_if_error: false
  env:
    CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}
```

**Why It Helps:**
- Tracks coverage over time
- Same Codecov repo as Python; different `flags` (go vs python)

---

## 4. Key Decisions

### Versioning Strategy: CalVer (same as Python)

- Same two tags as Python: `latest` + `YYYY.MM.DD`
- `latest` only on main/master branch
- Date tag only (no SHA) — keeps tagging simple and consistent

### Workflow Triggers

- Same branches as Python: `main`, `master`, `lab3`
- Path filters so only `app_go/**` and the workflow file trigger Go CI
- Pull requests to main/master also trigger the workflow when Go files change

### Test Coverage

- Go built-in coverage: `go test -coverprofile=coverage.out`
- Upload to Codecov with flag `go` for separate reporting from Python
- No strict fail-under in workflow; can be added in `go test` if needed

---

## 5. Path Filters & Multi-App CI

### Why Path Filters Matter

In a monorepo with `app_python/` and `app_go/`:
- Changes only in `app_python/` → only Python CI runs
- Changes only in `app_go/` → only Go CI runs
- Changes in both → both workflows run in parallel
- Changes only in `labs/`, `README`, etc. → neither workflow runs

### Testing Path Filters

**Scenario 1: Python-only change**
```bash
echo "# comment" >> app_python/app.py
git add app_python/app.py && git commit -m "docs: comment in Python" && git push
```
- **Result:** Python CI runs, Go CI does not run

**Scenario 2: Go-only change**
```bash
echo "// comment" >> app_go/main.go
git add app_go/main.go && git commit -m "docs: comment in Go" && git push
```
- **Result:** Go CI runs, Python CI does not run

**Scenario 3: Both apps changed**
```bash
# Modify both app_python and app_go, then push
```
- **Result:** Both Python CI and Go CI run (in parallel)

### Benefits

- **CI minutes:** Fewer unnecessary runs
- **Feedback:** Only relevant workflow runs for your changes
- **Clarity:** Actions tab shows only relevant jobs
- **Independence:** Python and Go can be developed and released independently

When you push only Python changes, only **Python CI/CD** runs. When you change files in both `app_python/` and `app_go/`, both workflows run (in parallel). This confirms path filters work as intended.

---

## 6. Test Coverage (Go)

### Coverage Tool

- **Tool:** Go built-in (`go test -coverprofile=coverage.out`)
- **Report:** `go tool cover -html=coverage.out` (local); Codecov (CI)

### CI Integration

- Coverage generated in the test job
- Uploaded to Codecov with `flags: go` and `file: ./app_go/coverage.out`
- Same `CODECOV_TOKEN` as for Python; repo can show both Python and Go coverage
- **Coverage dashboard:** [Codecov — DevOps-Core-Course (flag: go)](https://codecov.io/gh/karishka1222/DevOps-Core-Course)

### Coverage Analysis

**Current coverage:** 75.3% (total statements; target minimum 70%).

| Function         | Coverage | Notes                                      |
|-----------------|----------|--------------------------------------------|
| mainHandler     | 100%     | Main endpoint, incl. JSON write error path |
| healthHandler   | 100%     | Health endpoint, incl. JSON write error    |
| notFoundHandler | 100%     | 404 handler, incl. JSON write error        |
| getRequestInfo  | 100%     | Request parsing, X-Forwarded-For, User-Agent |
| getSystemInfo   | 100%     | Incl. hostname error fallback to "unknown" |
| formatUptime    | 100%     | All branches (seconds/minutes/hours, plural) |
| getUptime       | 100%     | Delegates to formatUptime                  |
| main            | 0%       | Entry point, not unit-tested               |

**What's not covered (and why):**
- `main` — server entry point; tested by integration/run, not unit tests.

**Coverage threshold:** Minimum 70%. Codecov tracks trends; all handlers and helpers are fully covered, including error paths (hostname failure, JSON write failure).

---

## 7. Challenges

- **Snyk for Go:** May require correct `SNYK_TOKEN` and project setup; `continue-on-error: true` avoids failing the workflow if Snyk is not configured.
- **golangci-lint:** Long timeout (`--timeout=5m`) avoids flaky failures on first run or large codebase.
- **Path filters:** Ensure changes you expect to trigger Go CI touch `app_go/**` or `.github/workflows/go-ci.yml`.
