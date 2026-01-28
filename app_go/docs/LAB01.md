# Lab 1 Bonus — Go Implementation

## Overview

Same DevOps Info Service as the Python app: `GET /` (service + system + runtime + request + endpoints) and `GET /health` (health check). Implemented in Go using only the standard library.

## Implementation details

- **`main.go`** — Single binary. Handlers: `mainHandler` for `/`, `healthHandler` for `/health`. `/health` is registered first so it is matched before `/`.
- **System info** — `os.Hostname()`, `runtime.GOOS` / `GOARCH` / `NumCPU()` / `Version()`. `platform_version` comes from `/etc/os-release` (`PRETTY_NAME`) on Linux; otherwise `runtime.GOOS`.
- **Uptime** — `startTime` stored at startup; duration computed on each request. Same human-readable format as Python (`"X hours, Y minutes"`).
- **Request info** — Client IP from `RemoteAddr` (or `X-Forwarded-For`), `User-Agent`, method, path.
- **Config** — `HOST` and `PORT` via env; defaults `0.0.0.0` and `5000`.

## JSON structure

Matches the Python shape. Differences:

- **`system.go_version`** — Go version (e.g. `1.24.2`) instead of `python_version`.
- **`service.framework`** — `"net/http"` (stdlib) instead of `"Flask"`.

## Build and run

```bash
cd app_go
go build -ldflags="-s -w" -o devops-info-service .
./devops-info-service
```

```bash
curl -s http://localhost:5000/ | jq
curl -s http://localhost:5000/health | jq
```

## Binary size vs Python

| Build | Size (approx.) |
|-------|----------------|
| `go build` | ~8.1 MB |
| `go build -ldflags="-s -w"` | ~5.5 MB |

Python runs via interpreter + venv; there is no single executable. The Go binary is self-contained and suitable for minimal container images.

## Screenshots

Place in `app_go/docs/screenshots/`:

- Main endpoint (`GET /`) — full JSON.
- Health check (`GET /health`) — JSON response.
- Formatted output (e.g. `curl … | jq`) or browser.

Build and run the binary, then capture these to complete the bonus submission.
