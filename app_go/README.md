# DevOps Info Service (Go)

Go implementation of the DevOps Info Service using standard `net/http` library.

## Prerequisites

- **Go**: 1.21 or higher

## Building

```bash
# Standard build
go build -o devops-info-service main.go

# Optimized build (smaller size)
go build -ldflags="-s -w" -o devops-info-service main.go
```

## Running

```bash
# Default (port 8080)
./devops-info-service

# Custom port
PORT=8090 ./devops-info-service

# Or run directly
go run main.go
```

## API Endpoints

### `GET /`

Returns service and system information.

**Request:**
```bash
curl http://localhost:8080/
```

**Response:**
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Go net/http"
  },
  "system": {
    "hostname": "MacBook-Pro--Egor.local",
    "platform": "darwin",
    "platform_version": "go1.25.6",
    "architecture": "arm64",
    "cpu_count": 11,
    "go_version": "go1.25.6"
  },
  "runtime": {
    "uptime_seconds": 41,
    "uptime_human": "0 minutes",
    "current_time": "2026-01-27T12:51:18.492136Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "[::1]:58274",
    "user_agent": "curl/8.7.1",
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

Health check endpoint.

**Request:**
```bash
curl http://localhost:8080/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-27T12:51:25.44394Z",
  "uptime_seconds": 48
}
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8080` | Server port |

## Comparison with Python

**Size:**
- Go binary: 5.2 MB
- Python venv: 21 MB

**Memory:**
- Go: 7 MB RSS
- Python: 35.5 MB RSS

**Advantages:**
- Single binary deployment
- No external dependencies
- Faster startup (~10-20ms vs ~300-500ms)
- Lower memory footprint
