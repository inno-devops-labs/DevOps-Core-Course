# LAB01 - DevOps Info Service (Go)

## Implementation Notes
This version mirrors the Python API and keeps the same JSON shape. The `python_version` field is kept for compatibility, and I fill it with the Go runtime version so the field is still informative.

## Build and Run
```bash
go run main.go
```

Build a binary:
```bash
go build -o devops-info
./devops-info
```

## Binary Size Comparison
- Go binary: `<size>`
- Python app (source only): `<size>`

Quick size commands:
```bash
ls -lh devops-info
dir devops-info.exe
```

## API Endpoints
### `GET /`
Returns service, system, runtime, and request details.

Example:
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Go net/http"
  },
  "system": {
    "hostname": "my-machine",
    "platform": "windows",
    "platform_version": "Windows_NT",
    "architecture": "amd64",
    "cpu_count": 12,
    "python_version": "go1.22.1"
  },
  "runtime": {
    "uptime_seconds": 42,
    "uptime_human": "0 hours, 0 minutes",
    "current_time": "2026-01-27T10:15:00Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/8.5.0",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/health", "method": "GET", "description": "Health check"}
  ]
}
```

### `GET /health`
Example:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-27T10:15:05Z",
  "uptime_seconds": 47
}
```

## Challenges & Solutions
- The Go mux treats `/` as a catch-all, so I added explicit path checks to return a JSON 404 for unknown routes.
- `RemoteAddr` includes the port, so I split host/port to get a clean client IP.
