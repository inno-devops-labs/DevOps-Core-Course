# DevOps Info Service (Go)

A high-performance Go implementation of the DevOps Info Service. Compiled to a single static binary with zero dependencies.

## Overview

This service provides the same functionality as the Python version but:
- **Faster** - Compiled native code
- **Smaller** - Single binary, no runtime
- **Efficient** - Lower memory footprint
- **Portable** - No dependencies to install

## Prerequisites

- **Go 1.21+**

## Installation

### Option 1: Build from source

```bash
cd app_go
go build -o devops-info-service main.go
```

### Option 2: Build optimized binary

```bash
# Smaller binary with stripped debug info
go build -ldflags="-s -w" -o devops-info-service main.go
```

### Option 3: Cross-compile for different platforms

```bash
# For Linux
GOOS=linux GOARCH=amd64 go build -o devops-info-service-linux main.go

# For Windows
GOOS=windows GOARCH=amd64 go build -o devops-info-service.exe main.go

# For macOS ARM (M1/M2)
GOOS=darwin GOARCH=arm64 go build -o devops-info-service-darwin main.go
```

## Running the Application

### Run directly with go

```bash
go run main.go
```

### Run compiled binary

```bash
# Default (0.0.0.0:5000)
./devops-info-service

# Custom port
PORT=8080 ./devops-info-service

# Custom host and port
HOST=127.0.0.1 PORT=3000 ./devops-info-service
```

## API Endpoints

### `GET /`
Returns comprehensive service and system information.

```bash
curl http://localhost:5000/
```

**Response includes:**
- Service metadata (name, version, framework: "Go net/http")
- System info (hostname, platform, architecture, CPU count, Go version)
- Runtime metrics (uptime, current time, timezone)
- Request details (client IP, user agent, method, path)
- Available endpoints

### `GET /health`
Health check endpoint for monitoring.

```bash
curl http://localhost:5000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-26T07:32:24Z",
  "uptime_seconds": 42
}
```

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `5000`    | Server port number  |

**Note:** DEBUG mode not needed in Go (controlled by build tags)

## Binary Size Comparison

Typical sizes after compilation:

```bash
# Python (with interpreter + dependencies)
~50-100 MB (Python runtime + packages)

# Go (optimized build)
~7-10 MB (single static binary)

# Go (with debug info)
~12-15 MB
```

**Size reduction:** ~90% smaller than Python deployment!

## Performance

Go advantages:
- **Startup time:** <10ms (vs ~500ms for Python)
- **Memory usage:** ~10-20MB (vs ~50-80MB for Python)
- **Request latency:** ~0.5ms (vs ~2-5ms for Python)
- **Concurrency:** Native goroutines (vs GIL in Python)

## Testing

```bash
# Test endpoints
curl http://localhost:5000/
curl http://localhost:5000/health

# Pretty-print JSON
curl -s http://localhost:5000/ | jq

# Load testing
ab -n 1000 -c 10 http://localhost:5000/
```

## Troubleshooting

**Go not installed:**
```bash
# macOS
brew install go

# Linux
sudo apt install golang-go

# Or download from: https://go.dev/dl/
```

**Port already in use:**
```bash
PORT=8080 ./devops-info-service
```

**Build errors:**
```bash
# Clean and rebuild
go clean
go build main.go
```

## Project Structure

```
app_go/
├── main.go              # Main application (only file needed!)
├── go.mod               # Module definition
├── .gitignore           # Git ignore patterns
├── README.md            # This file
└── docs/
    ├── LAB01.md        # Implementation details
    ├── GO.md           # Language justification
    └── screenshots/    # Evidence
```


