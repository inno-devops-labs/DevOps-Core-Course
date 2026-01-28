# LAB 1 — DevOps Info Service (Go Bonus)

## 1. Language Choice (Go)

For the compiled implementation I chose **Go**. It is well suited for small HTTP services because:

- It produces small, static binaries that are easy to ship in Docker images.
- The standard library includes a solid `net/http` package, so no heavy frameworks are required.
- Compiles quickly and has good performance for concurrent workloads.

## 2. Implementation Overview

The Go service exposes the same endpoints and similar JSON structure as the Python/Flask version:

- `GET /` — returns `service`, `system`, `runtime`, `request`, `endpoints`.
- `GET /health` — returns `status`, `timestamp`, `uptime_seconds`.

The uptime is calculated from a `startTime` global set at application start. System information uses values from the Go runtime (OS, architecture, CPU count, Go version) and the OS hostname.

## 3. Build and Run

```bash
cd app_go

# Run directly (development)
go run ./...

# Build binary
mkdir -p bin
go build -o bin/devops-info-service-go ./...

# Run with default configuration (PORT=5002)
./bin/devops-info-service-go

# Custom port
PORT=8080 ./bin/devops-info-service-go
```

## 4. API Documentation

### `GET /`

Example (shortened):

```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "framework": "net/http"
  },
  "system": {
    "platform": "linux",
    "architecture": "amd64",
    "cpu_count": 8,
    "go_version": "go1.22.0"
  },
  "runtime": {
    "uptime_seconds": 120,
    "uptime_human": "0 hours, 2 minutes"
  },
  "request": {
    "client_ip": "127.0.0.1:53412",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {"path": "/", "method": "GET"},
    {"path": "/health", "method": "GET"}
  ]
}
```

### `GET /health`

```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T12:00:00.000000Z",
  "uptime_seconds": 360
}
```

### Testing Commands

```bash
# Main endpoint
curl -s http://localhost:5002/ | jq

# Health check
curl -s http://localhost:5002/health | jq
```

## 5. Binary Size Comparison

After building both implementations in release mode (Python in a slim image and Go as a static binary) you can compare image or binary sizes:

- Go binary `bin/devops-info-service-go` is typically much smaller than a full Python runtime + dependencies.
- This makes multi‑stage Docker builds efficient: first stage builds the Go binary, second stage copies only the small binary.

## 6. Screenshots

Screenshots for the Go version can be stored in `app_go/docs/screenshots/`:

- `01-main-endpoint-go.png` — `/` response
- `02-health-check-go.png` — `/health` response

## 7. GitHub Community

Starring repositories is important in open source because it shows maintainers that their work is useful and increases the visibility of good projects for the wider community. Following developers (professors, TAs, and classmates) helps you discover new projects, learn from real-world commits, and build a professional network that makes teamwork and long‑term career growth easier.
