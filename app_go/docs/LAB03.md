# Lab 03 Bonus — Go CI with Path Filters & Coverage

## Second Workflow: Go CI

**File:** `.github/workflows/go-ci.yml`

### Language-Specific Best Practices

- **golangci-lint** — industry-standard Go linter (via `golangci/golangci-lint-action@v6`), checks for bugs, style issues, and unused code
- **go test -v** — built-in testing framework with verbose output
- **go test -coverprofile** — native coverage profiling, no external tools needed
- **Multi-stage Docker build** — builder (golang:1.23-alpine) → runtime (alpine:3.19)
- **Static binary** — `CGO_ENABLED=0` produces binary with no external dependencies

### Versioning Strategy: CalVer (consistent with Python)

Same strategy as Python for consistency:
- `aezuraa/devops-info-service:go` — rolling latest
- `aezuraa/devops-info-service:go-2026.02.10` — CalVer date
- `aezuraa/devops-info-service:go-abc1234` — commit SHA

## Path Filter Configuration

### Python Workflow

```yaml
on:
  push:
    paths:
      - 'app_python/**'
      - '.github/workflows/python-ci.yml'
```

### Go Workflow

```yaml
on:
  push:
    paths:
      - 'app_go/**'
      - '.github/workflows/go-ci.yml'
```

### How It Works

| Files Changed | Python CI | Go CI |
|---------------|-----------|-------|
| `app_python/app.py` | Runs | Skipped |
| `app_go/main.go` | Skipped | Runs |
| Both apps | Runs | Runs (parallel) |
| `README.md` only | Skipped | Skipped |

### Why Path Filters Matter in Monorepos

- **Save CI minutes:** No unnecessary builds when unrelated code changes
- **Faster feedback:** Each app's CI runs independently and in parallel
- **Less noise:** Developers only see relevant workflow results
- **Cost efficiency:** GitHub Actions billing is per-minute; fewer runs = lower costs

## Coverage Analysis

### Go Coverage: 75.9%

```
devops-info-service/main.go:68:     getHostname     75.0%
devops-info-service/main.go:76:     getUptime       100.0%
devops-info-service/main.go:104:    getClientIP     100.0%
devops-info-service/main.go:116:    mainHandler     100.0%
devops-info-service/main.go:173:    healthHandler   100.0%
devops-info-service/main.go:189:    notFoundHandler 100.0%
devops-info-service/main.go:198:    main            0.0%
total:                              (statements)    75.9%
```

### What's Covered (100%)

- `mainHandler` — GET /, JSON structure, all fields, content type
- `healthHandler` — GET /health, status, timestamp, uptime
- `notFoundHandler` — 404 response, JSON error
- `getUptime` — all branches (minutes only, hours+minutes, singular/plural)
- `getClientIP` — direct IP, X-Real-IP, X-Forwarded-For headers

### What's Not Covered and Why

- **`main()` — 0%:** Starts HTTP server with `ListenAndServe`. This is a blocking call that can't be unit-tested without spawning a full server. Standard practice is to exclude `main()` from coverage.
- **`getHostname()` error branch — 75%:** The `os.Hostname()` error path requires OS-level failure that can't be reliably simulated in tests.

### Coverage Threshold

Go CI does not enforce a hard threshold since `main()` (0%) disproportionately affects the number. Effective coverage of testable code is **~90%**.

### Test Summary

**22 tests, all passing:**

```
=== RUN   TestMainHandler_StatusCode           --- PASS
=== RUN   TestMainHandler_ContentType          --- PASS
=== RUN   TestMainHandler_ServiceFields        --- PASS
=== RUN   TestMainHandler_SystemFields         --- PASS
=== RUN   TestMainHandler_RuntimeFields        --- PASS
=== RUN   TestMainHandler_RequestFields        --- PASS
=== RUN   TestMainHandler_Endpoints            --- PASS
=== RUN   TestHealthHandler_StatusCode         --- PASS
=== RUN   TestHealthHandler_ContentType        --- PASS
=== RUN   TestHealthHandler_Fields             --- PASS
=== RUN   TestNotFoundHandler                  --- PASS
=== RUN   TestMainHandler_NotFoundForWrongPath --- PASS
=== RUN   TestGetHostname                      --- PASS
=== RUN   TestGetUptime                        --- PASS
=== RUN   TestGetClientIP                      --- PASS
=== RUN   TestGetClientIP_XRealIP              --- PASS
=== RUN   TestGetClientIP_XForwardedFor        --- PASS
=== RUN   TestGetUptime_WithHours              --- PASS
=== RUN   TestGetUptime_ExactlyOneHourOneMinute--- PASS
=== RUN   TestGetUptime_ExactlyOneMinute       --- PASS
PASS    coverage: 75.9% of statements    0.542s
```

## Codecov Integration

Both workflows upload coverage reports to Codecov:

```yaml
- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v4
  with:
    file: app_go/coverage.out
    flags: go
    token: ${{ secrets.CODECOV_TOKEN }}
```

Flags (`python` / `go`) allow tracking coverage per-app separately in Codecov dashboard.
