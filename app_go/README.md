# DevOps Info Service (Go)

A production-ready Go web service that provides comprehensive information about itself and its runtime environment. This is the compiled language version of the Python service, demonstrating multi-stage Docker build capabilities.

## Overview

The Go implementation of the DevOps Info Service is a lightweight, high-performance REST API that returns detailed system information, health status, and service metadata. This version demonstrates the advantages of compiled languages for containerized applications.

## Prerequisites

- Go 1.21 or higher

## Building

### Build for current platform
```bash
go build -o devops-info-service main.go
```

### Build for specific platforms
```bash
# Linux
GOOS=linux GOARCH=amd64 go build -o devops-info-service-linux main.go

# macOS (Apple Silicon)
GOOS=darwin GOARCH=arm64 go build -o devops-info-service-darwin-arm64 main.go

# macOS (Intel)
GOOS=darwin GOARCH=amd64 go build -o devops-info-service-darwin-amd64 main.go

# Windows
GOOS=windows GOARCH=amd64 go build -o devops-info-service.exe main.go
```

## Running the Application

### Using go run
```bash
go run main.go
```

### Using compiled binary
```bash
./devops-info-service
```

### With custom configuration
```bash
# Custom port
PORT=9090 go run main.go

# Custom host and port
HOST=127.0.0.1 PORT=3000 go run main.go
```

## API Endpoints

### GET /

Returns comprehensive service and system information.

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
    "hostname": "Mac",
    "platform": "darwin",
    "platform_version": "unknown",
    "architecture": "arm64",
    "cpu_count": 10,
    "go_version": "go1.24.0"
  },
  "runtime": {
    "uptime_seconds": 27,
    "uptime_human": "27 seconds",
    "current_time": "2026-01-27T19:29:02Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/8.7.1",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {
      "path": "/",
      "method": "GET",
      "description": "Service information"
    },
    {
      "path": "/health",
      "method": "GET",
      "description": "Health check"
    }
  ]
}
```

### GET /health

Simple health check endpoint for monitoring and Kubernetes probes.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-27T20:04:18Z",
  "uptime_seconds": 84
}
```

## Configuration

The application can be configured via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Host to bind the server to |
| `PORT` | `8080` | Port number for the server |

## Binary Size Comparison

| Language | Binary Size | Startup Time | Memory Usage |
|----------|-------------|--------------|--------------|
| **Go** | ~2-3 MB | Instant | ~2-3 MB |
| Python | N/A (interpreter) | ~100ms | ~20-30 MB |

## Advantages of Go Implementation

1. **Small Binary Size**: The compiled binary is only 2-3 MB, compared to Python's interpreter + dependencies
2. **Fast Startup**: Instant startup time vs Python's interpreter overhead
3. **Low Memory Usage**: Significantly lower memory footprint
4. **Single Binary**: No dependencies to manage, just copy the binary
5. **Cross-Compilation**: Easily build for any platform from any machine
6. **Performance**: Better performance and concurrency support

## Project Structure

```
app_go/
├── main.go                  # Main application
├── go.mod                   # Go module definition
├── README.md                # This file
└── docs/                    # Lab documentation
    ├── LAB01.md            # Implementation details
    ├── GO.md               # Language justification
    └── screenshots/        # Proof of work
```

## Examples

### Testing with curl
```bash
# Main endpoint
curl http://localhost:8080/

# Health check
curl http://localhost:8080/health

# Pretty print JSON
curl http://localhost:8080/ | jq
```

### Build and run
```bash
# Build
go build -o devops-info-service main.go

# Run
./devops-info-service

# Test
curl http://localhost:8080/
```

## Future Enhancements

This Go implementation will be used in Lab 2 to demonstrate:
- Multi-stage Docker builds
- Smaller final image size
- Static binary compilation
- Alpine-based containers

## License

Educational use for DevOps course.
