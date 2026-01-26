# DevOps Info Service - Go Implementation

A production-ready web service providing detailed information about itself and its runtime environment. This is the Go implementation of the DevOps Info Service, built for Lab 1 bonus task.

## Overview

The DevOps Info Service exposes REST API endpoints that return:
- Service metadata (name, version, framework)
- System information (hostname, platform, CPU, Go version)
- Runtime metrics (uptime, current time)
- Request details (client IP, user agent)
- Health status for monitoring

## Prerequisites

- Go 1.21 or higher

## Installation

1. **Navigate to the project directory**:
   ```bash
   cd app_go
   ```

2. **Download dependencies** (if any):
   ```bash
   go mod tidy
   ```

## Building

### Development Build
```bash
go build -o devops-info-service main.go
```

### Production Build (Optimized)
```bash
CGO_ENABLED=0 go build -ldflags="-s -w" -o devops-info-service main.go
```

## Running the Application

### Using go run
```bash
go run main.go
# Server runs on http://0.0.0.0:8080
```

### Using the binary
```bash
./devops-info-service
```

### Custom Port
```bash
PORT=5000 go run main.go
# Server runs on http://0.0.0.0:5000
```

### Custom Host and Port
```bash
HOST=127.0.0.1 PORT=3000 go run main.go
# Server runs on http://127.0.0.1:3000
```

## API Endpoints

### `GET /` - Service Information

Returns comprehensive service and system information.

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
    "framework": "net/http"
  },
  "system": {
    "hostname": "my-laptop",
    "platform": "linux",
    "platform_version": "linux/amd64",
    "architecture": "amd64",
    "cpu_count": 8,
    "go_version": "go1.21.0"
  },
  "runtime": {
    "uptime_seconds": 3600,
    "uptime_human": "1 hour, 0 minutes",
    "current_time": "2026-01-26T16:30:00Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1:54321",
    "user_agent": "curl/7.81.0",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/health", "method": "GET", "description": "Health check"}
  ]
}
```

### `GET /health` - Health Check

Simple health endpoint for monitoring and Kubernetes probes.

**Request:**
```bash
curl http://localhost:8080/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-26T16:30:00Z",
  "uptime_seconds": 3600
}
```

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `HOST` | `0.0.0.0` | Host address to bind |
| `PORT` | `8080` | Port number to listen on |

## Binary Size Comparison

| Implementation | Binary/Dependencies Size |
|---------------|-------------------------|
| Go (optimized) | ~5-6 MB (single binary) |
| Python + venv | ~50+ MB (interpreter + deps) |

Go produces a single static binary with no external dependencies, ideal for containerization.

## Project Structure

```
app_go/
├── main.go              # Main application
├── go.mod               # Go module definition
├── README.md            # This file
└── docs/
    ├── LAB01.md        # Implementation details
    ├── GO.md           # Language justification
    └── screenshots/    # Proof of work
```

## Future Enhancements

This service will be extended in future labs:
- Lab 2: Docker multi-stage build
- Lab 3: Unit tests and CI/CD
- Lab 8: Prometheus metrics endpoint
- Lab 9: Kubernetes deployment
