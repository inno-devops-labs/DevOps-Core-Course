# DevOps Info Service (Lab 01) — Go version

Small Go web app for DevOps labs (extra points).

Provides:
- `GET /` — service/system/runtime/request info + list of endpoints
- `GET /health` — simple health check endpoint (for monitoring / K8s probes)

Configuration is done via environment variables: `HOST`, `PORT`, `DEBUG`.

---

## Overview

This service returns diagnostic information about:
- service metadata (name/version/description/framework)
- host system (hostname/platform/arch/CPU/Go version)
- runtime (uptime + current UTC time)
- current request (client IP, user-agent, method, path)
- available API endpoints (kept as a registry in the app and returned sorted)

---

## Prerequisites

- Go **1.20+** (any modern Go should work)
- No third-party dependencies (standard library only)

---

## Quick Start (go run)
If `go.mod` is missing, you can create it:

```bash
go mod init devops-info-service
```
From the directory containing `main.go`:

Default (0.0.0.0:5000):
```bash
go run .
# or: go run main.go
```

Custom port:
```bash
PORT=8080 go run .
```

Custom host + port:
```bash
HOST=127.0.0.1 PORT=3000 go run .
```

Enable debug-style logging:
```bash
DEBUG=true go run .
```

---

## Build (Binary)

1. Initialize modules (if needed):
```bash
go mod init devops-info-service
go mod tidy
```
2. Build a local binary:
```bash
go build -o devops-info-service .
```
3. Run the binary:
```bash
./devops-info-service
# or with config:
HOST=127.0.0.1 PORT=3000 DEBUG=true ./devops-info-service
```
---

## API Endpoints

### `GET /`

Returns full service + runtime info.

Example:
```bash
curl -s http://127.0.0.1:5000/ | jq '{service, system, runtime, request, endpoints}'
```

Response structure:
```json
{
    "service": {
        "name": "devops-info-service",
        "version": "1.0.0",
        "description": "DevOps course info service",
        "framework": "Go net/http"
    },
    "system": {
        "hostname": "SerggAidd",
        "platform": "linux",
        "platform_version": "6.18.5-arch1-1",
        "architecture": "amd64",
        "cpu_count": 24,
        "go_version": "go1.25.5 X:nodwarf5"
    },
    "runtime": {
        "uptime_seconds": 3,
        "uptime_human": "0 hour, 0 minutes",
        "current_time": "2026-01-23T19:08:17Z",
        "timezone": "UTC"
    },
    "request": {
        "client_ip": "127.0.0.1",
        "user_agent": "curl/8.18.0",
        "method": "GET",
        "path": "/"
    },
    "endpoints": [
        {
            "method": "GET",
            "path": "/",
            "description": "Root endpoint: returns service metadata and diagnostic information."
        },
        {
            "method": "GET",
            "path": "/health",
            "description": "Health check endpoint for monitoring and Kubernetes probes."
        }
    ]
}
```

> Note: JSON object key ordering is not guaranteed by the HTTP/JSON standard.
> Use `python -m json.tool` or `jq` (like in example) only for pretty printing.

---

### `GET /health`

Health endpoint for monitoring / Kubernetes probes.

Example:
```bash
curl -s http://127.0.0.1:5000/health | python -m json.tool
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-23T19:08:22Z",
  "uptime_seconds": 8
}
```

Always returns HTTP **200** when the service is running.

---

## Error Handling

- Unknown routes return JSON 404:

Example:
```bash
curl -s http://127.0.0.1:5000/does-not-exist | python -m json.tool
```

Response:
```json
{
  "error": "Not Found",
  "message": "Endpoint does not exist"
}
```

- Internal errors return JSON 500 (panic is recovered by middleware):

Example (can be tested by uncommenting the code block with the corresponding endpoint):
```bash
curl -s http://127.0.0.1:5000/crash | python -m json.tool
```

Response:
```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred"
}
```

---

## Logging

The app logs to **stdout**, which is the recommended approach for Docker/Kubernetes.

Logged events:
- request method/path/client IP/user-agent
- final HTTP status code and request latency
- recovered panics (500) with a short error message

---

## Configuration

| Variable | Default   | Description |
|---------:|-----------|-------------|
| `HOST`   | `0.0.0.0` | Bind address |
| `PORT`   | `5000`    | Listen port |
| `DEBUG`  | `False`   | `true` enables more verbose log flags |
