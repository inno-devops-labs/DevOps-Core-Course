# DevOps Info Service (Go)

![Go CI](https://github.com/AEZuraa/DevOps-Core-Course/actions/workflows/go-ci.yml/badge.svg)
[![codecov](https://codecov.io/gh/AEZuraa/DevOps-Core-Course/branch/lab03/graph/badge.svg?flag=go)](https://codecov.io/gh/AEZuraa/DevOps-Core-Course)

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

### `GET /visits`

Returns the current visit counter. The counter increments on each `GET /` request and persists to `/data/visits`.

**Request:**
```bash
curl http://localhost:8080/visits
```

**Response:**
```json
{
  "visits": 42
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
| `VISITS_FILE` | `/data/visits` | Path to the visits counter file |

## Docker

### Build Multi-Stage Image

```bash
docker build -t aezuraa/devops-info-service:go .
```

### Run Container

```bash
docker run -p 8080:8080 aezuraa/devops-info-service:go
```

### Pull from Docker Hub

```bash
docker pull aezuraa/devops-info-service:go
docker run -p 8080:8080 aezuraa/devops-info-service:go
```

### Custom Port

```bash
docker run -p 8090:8090 -e PORT=8090 aezuraa/devops-info-service:go
```

## Testing

```bash
# Run tests
go test -v ./...

# Run tests with coverage
go test -v -coverprofile=coverage.out ./...
go tool cover -func=coverage.out
```

## Comparison with Python

**Binary Size:**
- Go: 5.2 MB
- Python venv: 21 MB

**Container Image Size:**
- Go (multi-stage): 26.2 MB (compressed 7.58 MB)
- Python: 223 MB (compressed 48.4 MB)

**Memory Usage (Running):**
- Go: 2.9 MB RSS
- Python: 39.4 MB RSS

**Advantages:**
- **8.5x smaller** container image
- **13.6x less memory** usage
- Single binary deployment
- No external dependencies
- Faster startup (~10-20ms vs ~200-300ms)
- Lower CPU usage
