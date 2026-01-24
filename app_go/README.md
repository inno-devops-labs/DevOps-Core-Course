# DevOps Info Service - Go

A high-performance web service implementing the same DevOps information API in Go. Demonstrates compiled language benefits: minimal resource usage, fast binary generation, and deployment simplicity.

## Overview

- **Service Information**: Application metadata and framework details
- **System Introspection**: Real-time OS, CPU, and system information
- **Runtime Monitoring**: Uptime tracking and ISO8601 timestamps
- **Health Checks**: Kubernetes-compatible readiness/liveness probe endpoint
- **Request Tracking**: Client IP, user agent, method, and path logging
- **Environment Configuration**: PORT customization via env vars
- **Single Binary**: No runtime dependencies, easy containerization

## Prerequisites

- **Go 1.20 or later**
- (Optional) **gcc** for cgo-based builds (standard Go doesn't require it)

## Installation

1. Navigate to the project directory:
```bash
cd app_go
```

2. Download dependencies:
```bash
go mod download
```

## Building

### Compile to Binary
```bash
go build -o devops-info-service main.go
```

## Running the Application

### Default Configuration (localhost:8080)
```bash
./devops-info-service
```

### Custom Port
```bash
PORT=5000 ./devops-info-service
```

## API Endpoints

### GET /

Returns comprehensive service and system information.

**Response (200 OK):**
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Go net/http"
  },
  "system": {
    "hostname": "LAPTOP-LJVRUS9G",
    "platform": "linux",
    "platform_version": "amd64",
    "architecture": "amd64",
    "cpu_count": 20,
    "go_version": "go1.21.8"
  },
  "runtime": {
    "uptime_seconds": 27,
    "uptime_human": "0 hours, 0 minutes",
    "current_time": "2026-01-24T17:34:51Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1:35002",
    "user_agent": "curl/7.81.0",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {
      "description": "Service information",
      "method": "GET",
      "path": "/"
    },
    {
      "description": "Health check",
      "method": "GET",
      "path": "/health"
    }
  ]
}
```

### GET /health

Simple health check endpoint for Kubernetes probes.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-24T17:34:33Z",
  "uptime_seconds": 9
}
```

## Binary Comparison

| Metric | Python | Go (optimized) |
|--------|--------|---|
| Binary Size | N/A (interpreted) | 6-8 MB |
| Startup Time | 1.5-2 sec | <10 ms |
| Memory (idle) | 50-80 MB | 1-2 MB |
| Memory (with requests) | Grows with concurrency | Constant |
| Deployment | Requires Python + deps | Single file |
| Cross-platform | Yes (if no native deps) | Easy (rebuild) |

## Performance Notes

- **Startup**: < 10 milliseconds
- **Response Time**: < 2ms for typical requests
- **Concurrent Requests**: Handles thousands with goroutines
- **Memory**: ~1-2 MB idle, minimal growth under load
- **CPU**: Single core efficient due to Go scheduler
