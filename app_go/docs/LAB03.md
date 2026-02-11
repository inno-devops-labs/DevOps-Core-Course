# Lab 3 — Go CI/CD (Bonus)

## Overview

Go CI workflow at `.github/workflows/go-ci.yml` mirrors the Python pipeline with language-specific tooling.

### Key Differences from Python CI

| Aspect | Python | Go |
|--------|--------|-----|
| Linter | flake8 | golangci-lint |
| Test runner | pytest | `go test` |
| Coverage | pytest-cov + Codecov | Built-in `go test -coverprofile` |
| Docker | Single-stage (python:3.13-slim) | Multi-stage (golang → scratch) |
| Caching | pip cache | Go module cache |

### Tests

Go tests are in `main_test.go` using the standard `testing` package and `net/http/httptest`:

- `TestMainHandler_StatusCode` — GET / → 200
- `TestMainHandler_JSON` — valid JSON, all top-level keys present
- `TestMainHandler_ServiceFields` — service name, version, framework
- `TestHealthHandler_StatusCode` — GET /health → 200
- `TestHealthHandler_JSON` — status "healthy", valid timestamp
- `TestNotFound` — unknown path → 404
- `TestGetUptime` / `TestGetHostname` — helper functions
- `TestContentType` — all handlers return `application/json`

### Path Filters

```yaml
paths:
  - 'app_go/**'
  - '.github/workflows/go-ci.yml'
```

Python workflow runs **only** on `app_python/` changes; Go workflow runs **only** on `app_go/` changes. Both can execute in parallel when both paths change in the same commit.

**Benefits of path-based triggers in monorepos:**
- Saves CI minutes — no redundant jobs
- Faster feedback — each app gets results without waiting for the other
- Cleaner logs — only relevant workflow appears

### Versioning

Same SemVer strategy as Python. Docker images tagged: `latest`, `1.0.0`, `<sha>`.
