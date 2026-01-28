# Go DevOps Info Service

> A Go implementation of the DevOps Info Service providing system information and health checks via HTTP.

## Overview

This is a pure Go HTTP server implementation using the standard library's `net/http` package. It provides the same functionality as the Flask version but with the benefits of a compiled language: single executable binary, faster startup, lower memory usage, and no runtime dependencies.

## Prerequisites

- **Go 1.21+** or later
- **Git** (for cloning)
- **Terminal/CLI** for running commands

## Installation

### 1. Navigate to the project directory

```bash
cd app_go
```

### 2. Download dependencies (if any)

```bash
go mod download
```

## Building the Application

### Development Mode

Run directly without compiling:

```bash
go run main.go
```

The server will start on `http://0.0.0.0:8080` by default.

### Production Build

Compile to a binary executable:

```bash
# Basic build
go build -o devops-info-service main.go

# Run the compiled binary
./devops-info-service

# With custom configuration
PORT=3000 ./devops-info-service
HOST=127.0.0.1 PORT=5000 ./devops-info-service
```

### Cross-Platform Builds

Build for different operating systems:

```bash
# Build for macOS (Intel)
GOOS=darwin GOARCH=amd64 go build -o devops-info-service-macos

# Build for macOS (Apple Silicon)
GOOS=darwin GOARCH=arm64 go build -o devops-info-service-arm64

# Build for Linux
GOOS=linux GOARCH=amd64 go build -o devops-info-service-linux

# Build for Windows
GOOS=windows GOARCH=amd64 go build -o devops-info-service.exe
```

## Custom Configuration

Configure the application using environment variables:

```bash
# Run on a different port
PORT=3000 go run main.go

# Run on localhost only
HOST=127.0.0.1 go run main.go

# Enable debug logging
DEBUG=true go run main.go

# Combine multiple settings
HOST=127.0.0.1 PORT=9000 DEBUG=true go run main.go
```

## API Endpoints

### `GET /`

Returns comprehensive service and system information.

**Request:**
```bash
curl http://localhost:8080/
```

**Response Example:**

```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Go (http)"
  },
  "system": {
    "hostname": "MacBook-Pro.local",
    "platform": "darwin",
    "platform_version": "go1.21.0",
    "architecture": "arm64",
    "cpu_count": 8,
    "go_version": "1.21.0"
  },
  "runtime": {
    "uptime_seconds": 42,
    "uptime_human": "0 hours, 0 minutes",
    "current_time": "2026-01-28T09:30:00.000000Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/8.4.0",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {
      "path": "/",
      "method": "GET",
      "description": "Service and system information"
    },
    {
      "path": "/health",
      "method": "GET",
      "description": "Health check endpoint"
    }
  ]
}
```

### `GET /health`

Health check endpoint for monitoring systems and Kubernetes probes.

**Request:**
```bash
curl http://localhost:8080/health
```

**Response Example:**

```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T09:30:00.000000Z",
  "uptime_seconds": 42
}
```

## Testing

### Using curl

```bash
# Test main endpoint
curl http://localhost:8080/

# Test health endpoint
curl http://localhost:8080/health

# Pretty-printed JSON (requires jq)
curl http://localhost:8080/ | jq .

# Test health endpoint with pretty output
curl http://localhost:8080/health | jq .

# Alternative: Pretty-print with Python3
curl http://localhost:8080/ | python3 -m json.tool
# Or with Python:
curl http://localhost:8080/ | python -m json.tool
```

### Using HTTPie

```bash
http http://localhost:8080/
http http://localhost:8080/health
```

### Using wget

```bash
wget -q -O - http://localhost:8080/
wget -q -O - http://localhost:8080/health
```

## Performance Comparison

### Binary Size

```bash
# Go (compiled binary)
ls -lh devops-info-service
# Output: ~6-7 MB (depending on OS/architecture)

# Python (Flask)
# Total with venv: ~100-150 MB
```

### Startup Time

```bash
# Go
time ./devops-info-service

# Python
time python app.py
```

Go is typically 10-100x faster to start.

### Memory Usage

```bash
# Monitor memory while running
top -p $(pgrep devops-info-service)  # Go
top -p $(pgrep python)               # Python
```

Go typically uses 5-10x less memory.

## Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server host address |
| `PORT` | `8080` | Server port number |
| `DEBUG` | `false` | Enable debug logging |

## Project Structure

```
app_go/
├── main.go              # Complete application
├── go.mod               # Go module definition
├── README.md            # This file
└── docs/
    ├── LAB01.md        # Lab submission report
    ├── GO.md           # Go language justification
    └── screenshots/     # Proof of work
```

## Code Organization

The Go implementation uses:

1. **Struct-based responses** - Type-safe JSON serialization
2. **Handler functions** - Standard Go HTTP pattern
3. **Standard library only** - No external dependencies
4. **Proper error handling** - Graceful error responses
5. **Concurrency-ready** - Goroutines handle concurrent requests

## Advantages of Go Implementation

1. **Single Binary** - No runtime dependencies, easy deployment
2. **Fast Compilation** - Quick build times
3. **Small Size** - ~6-7 MB vs 100+ MB for Python
4. **High Performance** - Handles more concurrent requests
5. **Low Memory** - 5-10x less memory than Python
6. **Production Ready** - Used by Docker, Kubernetes, etc.

## Disadvantages

1. **Steeper Learning Curve** - Different paradigm than Python
2. **Less Flexible** - More rigid type system
3. **Verbose** - More code for same functionality
4. **Smaller Ecosystem** - Fewer libraries than Python

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8080
lsof -i :8080

# Kill the process
kill -9 <PID>

# Or use a different port
PORT=9000 go run main.go
```

### Build Fails

```bash
# Make sure Go is installed
go version

# Update Go modules
go mod tidy

# Clean build cache
go clean
```

### Cannot Find Module

```bash
# Initialize go.mod (if missing)
go mod init devops-info-service

# Download dependencies
go mod download
```

## Next Steps

This Go implementation demonstrates:
- ✅ Pure standard library HTTP server
- ✅ JSON serialization
- ✅ System information gathering
- ✅ Environment variable configuration
- ✅ Production-ready compilation

This can be containerized with Docker in Lab 2 with multi-stage builds to create ultra-lightweight images.

## References

- [Go Documentation](https://golang.org/doc/)
- [net/http Package](https://pkg.go.dev/net/http)
- [encoding/json Package](https://pkg.go.dev/encoding/json)
- [Go Time Package](https://pkg.go.dev/time)
- [Go os Package](https://pkg.go.dev/os)
- [Go runtime Package](https://pkg.go.dev/runtime)

## Author

Created for DevOps Core Course - Lab 1 (Bonus Task)
