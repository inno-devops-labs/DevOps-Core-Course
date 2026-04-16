# DevOps Info Service - Go

[![Go CI](https://github.com/Arino4kaMyr/DevOps-Core-Course/actions/workflows/go-ci.yml/badge.svg)](https://github.com/Arino4kaMyr/DevOps-Core-Course/actions/workflows/go-ci.yml)
[![codecov](https://codecov.io/github/Arino4kaMyr/DevOps-Core-Course/graph/badge.svg?flag=go)](https://codecov.io/github/Arino4kaMyr/DevOps-Core-Course?flag=go)

A production-ready web service implemented in Go that provides comprehensive information about itself and its runtime environment. This is the compiled language version of the DevOps Info Service, built using Go's standard `net/http` package.

## Overview

The DevOps Info Service (Go version) is a RESTful API that exposes system information, runtime metrics, and health status. This implementation demonstrates the benefits of compiled languages: small binary size, fast execution, and single-file deployment.

**Key Features:**
- System information endpoint (`GET /`) — increments persistent visit counter
- Health check endpoint (`GET /health`)
- Visit counter endpoint (`GET /visits`) — returns total visit count
- Configurable via environment variables
- Single binary deployment (no runtime dependencies)
- Fast startup and execution
- Persistent visit counter stored on disk (survives restarts)

## Prerequisites

- **Go:** 1.21 or higher
- **Git:** For dependency management (if using external packages)

## Installation

### Option 1: Build from Source

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd DevOps-Core-Course/app_go
   ```

2. **Build the application:**
   ```bash
   go build -o devops-info-service main.go
   ```

3. **Run the binary:**
   ```bash
   ./devops-info-service
   ```

### Option 2: Install Directly

```bash
go install ./...
```

The binary will be installed to `$GOPATH/bin` (or `$HOME/go/bin` by default).

## Running the Application

### Basic Usage

Run the application with default settings (port: `8080`):

```bash
# If built locally
./devops-info-service

# Or run directly with go
go run main.go
```

### Custom Configuration

Configure the application using environment variables:

```bash
# Custom port
PORT=3000 ./devops-info-service

# Or with go run
PORT=3000 go run main.go
```

The service will be available at `http://0.0.0.0:<PORT>`

## API Endpoints

### `GET /`

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
    "hostname": "my-laptop",
    "platform": "darwin",
    "platform_version": "go1.21.0",
    "architecture": "arm64",
    "cpu_count": 8,
    "go_version": "go1.21.0"
  },
  "runtime": {
    "uptime_seconds": 3600.5,
    "uptime_human": "1 hour, 0 minutes, 0 seconds",
    "current_time": "2026-01-31T17:30:00.000Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/7.81.0",
    "method": "GET",
    "path": "/"
  },
  "visits": 42,
  "endpoints": [
    {"path": "/", "method": "GET", "description": "Service information + visit counter increment"},
    {"path": "/health", "method": "GET", "description": "Health check"},
    {"path": "/visits", "method": "GET", "description": "Current visit count"}
  ]
}
```

**Example Request:**
```bash
curl http://localhost:8080/
```

### `GET /visits`

Returns the current persistent visit count.

**Response:**
```json
{
  "visits": 42,
  "file": "/data/visits"
}
```

**Example Request:**
```bash
curl http://localhost:8080/visits
```

---

### `GET /health`

Simple health check endpoint for monitoring and Kubernetes probes.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-31T17:30:00.000Z",
  "uptime_seconds": 3600.5
}
```

**Status Codes:**
- `200 OK`: Service is healthy

**Example Request:**
```bash
curl http://localhost:8080/health
```

## Configuration

The application can be configured using the following environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8080` | Port number to listen on |
| `VISITS_FILE` | `/data/visits` | Path to the persistent visits counter file |

## Build Process

### Development Build

```bash
go build -o devops-info-service main.go
```

### Production Build (Optimized)

```bash
# Build with optimizations and smaller binary size
go build -ldflags="-s -w" -o devops-info-service main.go
```

**Build Flags:**
- `-ldflags="-s -w"`: Strip debug information and symbol table (reduces binary size)

### Cross-Platform Build

```bash
# Build for Linux
GOOS=linux GOARCH=amd64 go build -o devops-info-service-linux main.go

# Build for Windows
GOOS=windows GOARCH=amd64 go build -o devops-info-service.exe main.go

# Build for macOS (ARM)
GOOS=darwin GOARCH=arm64 go build -o devops-info-service-darwin-arm64 main.go
```

## Binary Size Comparison

### Go Binary Size

```bash
$ ls -lh devops-info-service
-rwxr-xr-x  1 user  staff   8.5M  devops-info-service

# With optimizations
$ go build -ldflags="-s -w" -o devops-info-service main.go
$ ls -lh devops-info-service
-rwxr-xr-x  1 user  staff   6.2M  devops-info-service
```

### Python Comparison

- **Go binary:** ~6-8 MB (single file, no dependencies)
- **Python application:** Requires Python runtime (~50-100 MB) + dependencies (~10-20 MB) = ~60-120 MB total

**Advantages of Go:**
- Single binary deployment (no runtime installation needed)
- Faster startup time
- Lower memory footprint
- Better suited for containerized deployments (smaller images)

## Running with Docker Compose

```bash
# Build and start (persists visits in ./data/visits)
docker compose up --build -d

# Check visits counter
curl http://localhost:8080/visits

# Access root endpoint a few times to increment counter
curl http://localhost:8080/

# Restart container and verify counter is preserved
docker compose restart
curl http://localhost:8080/visits

# View the counter file directly on the host
cat ./data/visits
```

## Project Structure

```
app_go/
├── main.go                 # Main application
├── go.mod                  # Go module definition
├── Dockerfile              # Multi-stage Docker build
├── docker-compose.yml      # Local development with persistent volume
├── README.md              # This file
├── data/                  # Persistent visits counter (git-ignored)
│   └── visits             # Counter file
└── docs/                  # Documentation
    ├── LAB01.md          # Lab submission documentation
    ├── GO.md             # Language justification
    └── screenshots/      # Screenshots and proof of work
```

## Dependencies

This implementation uses only Go's standard library:
- `net/http` - HTTP server and client
- `encoding/json` - JSON encoding/decoding
- `os` - Operating system interface
- `runtime` - Runtime information
- `time` - Time operations
- `fmt` - Formatted I/O
- `strings` - String manipulation

No external dependencies required! See `go.mod` for module definition.

## Development

### Unit Tests and Coverage

```bash
# Run tests
go test -v ./...

# Run tests with coverage
go test -coverprofile=coverage.out ./...
go tool cover -func=coverage.out
```

### Testing

Test the endpoints using curl:

```bash
# Test main endpoint
curl http://localhost:8080/ | jq

# Test health endpoint
curl http://localhost:8080/health | jq
```

Or use a browser to visit:
- `http://localhost:8080/`
- `http://localhost:8080/health`


## Docker

The application is available as a containerized Docker image using multi-stage builds for minimal size and maximum security.

### Running with Docker

Pull and run the image:

```bash
docker pull <your-dockerhub-username>/devops-go-multistage:latest
docker run -d -p 8080:8080 --name devops-go <your-dockerhub-username>/devops-go-multistage:latest
```

### Building Locally

Build the multi-stage Docker image:

```bash
docker build -t devops-go-multistage:latest .
```

Run the container:

```bash
docker run -d -p 8080:8080 --name devops-go devops-go-multistage:latest
```

### Testing the Container

```bash
# Health check
curl http://localhost:8080/health

# Service information
curl http://localhost:8080/ | jq
```

### Docker Image Features

- **Multi-Stage Build**: Separate build and runtime stages for minimal size
- **Size**: ~15MB (95% smaller than single-stage build)
- **Security**: Runs as non-root user, minimal attack surface
- **Base**: Alpine Linux 3.19 for small size and security
- **Health Check**: Built-in health monitoring for orchestration

For detailed documentation on the multi-stage build strategy, see [`docs/LAB02.md`](docs/LAB02.md).

---

## Advantages of Go Implementation

1. **Single Binary**: No runtime dependencies, easy deployment
2. **Fast Compilation**: Quick build times for rapid iteration
3. **Small Binary Size**: Efficient for containerized deployments
4. **Fast Execution**: Compiled code runs faster than interpreted languages
5. **Concurrent by Design**: Built-in goroutines for future scalability
6. **Cross-Platform**: Easy to build for multiple platforms

