# DevOps Info Service (Go)

[![Go CI](https://github.com/karishka1222/DevOps-Core-Course/actions/workflows/go-ci.yml/badge.svg?branch=lab3)](https://github.com/karishka1222/DevOps-Core-Course/actions/workflows/go-ci.yml)
[![codecov](https://codecov.io/gh/karishka1222/DevOps-Core-Course/branch/lab3/graph/badge.svg?flag=go)](https://codecov.io/gh/karishka1222/DevOps-Core-Course)
![Go Version](https://img.shields.io/badge/go-1.21%2B-00ADD8?logo=go)

A lightweight Go web service that provides comprehensive information about itself and its runtime environment. This is a compiled language implementation of the DevOps Info Service, offering improved performance and smaller deployment size.

## Overview

DevOps Info Service (Go version) is built using Go's standard `net/http` library, providing:
- Service metadata (name, version, framework)
- System information (hostname, platform, CPU, Go version)
- Runtime metrics (uptime, current time)
- Request details (client IP, user agent, method, path)
- Health status for monitoring tools

**Key Advantages:**
- Single binary with no dependencies
- Fast startup time (~milliseconds)
- Low memory footprint
- Easy deployment (just copy the binary)

## Prerequisites

- **Go:** 1.21 or higher
- **Operating System:** Linux, macOS, or Windows

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/karishka1222/DevOps-Core-Course.git
cd DevOps-Core-Course/app_go
```

### 2. Build the Application

```bash
# Build for your current platform
go build -o devops-info-service main.go

# Or simply
go build
```

### 3. Cross-Compilation Examples

Go makes it easy to compile for different platforms:

```bash
# Build for Linux (amd64)
GOOS=linux GOARCH=amd64 go build -o devops-info-service-linux main.go

# Build for macOS (arm64 - M1/M2/M3)
GOOS=darwin GOARCH=arm64 go build -o devops-info-service-macos main.go

# Build for Windows
GOOS=windows GOARCH=amd64 go build -o devops-info-service.exe main.go
```

## Running the Application

### Option 1: Run Directly with Go

```bash
go run main.go
```

### Option 2: Build and Run Binary

```bash
# Build
go build -o devops-info-service main.go

# Run
./devops-info-service
```

### Custom Configuration

Use environment variables to customize:

```bash
# Run on custom port
PORT=3000 ./devops-info-service

# Bind to localhost only
HOST=127.0.0.1 PORT=3000 ./devops-info-service
```

## API Endpoints

### GET /

**Description:** Returns comprehensive service and system information

**Example Request:**
```bash
curl http://localhost:8080/
```

**Example Response:**
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
    "platform_version": "darwin arm64",
    "architecture": "arm64",
    "cpu_count": 8,
    "go_version": "go1.21.0"
  },
  "runtime": {
    "uptime_seconds": 120,
    "uptime_human": "2 minutes",
    "current_time": "2026-01-27T14:30:00.000000000Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1:52334",
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

**Description:** Health check endpoint for monitoring

**Example Request:**
```bash
curl http://localhost:8080/health
```

**Example Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-27T14:30:00.000000000Z",
  "uptime_seconds": 120
}
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Host address to bind |
| `PORT` | `8080` | Port number to listen on |

## Testing the Service

```bash
# Test main endpoint
curl http://localhost:8080/

# Test health endpoint
curl http://localhost:8080/health

# Pretty-print JSON
curl http://localhost:8080/ | python -m json.tool

# Test 404 handling
curl http://localhost:8080/nonexistent
```

## Running Unit Tests

Go has built-in testing — no extra dependencies needed.

**Run all tests:**
```bash
cd app_go
go test ./...
```

**Run tests with verbose output:**
```bash
go test -v ./...
```

**Run tests with race detector and coverage:**
```bash
go test -v -race -coverprofile=coverage.out ./...
```

**View coverage report:**
```bash
# Terminal summary (after running with -coverprofile)
go tool cover -func=coverage.out

# HTML report (opens in browser)
go tool cover -html=coverage.out -o coverage.html
open coverage.html   # macOS
# or: xdg-open coverage.html   # Linux
```

**Test structure:**
- `main_test.go` — 7 test cases: main endpoint, health, system info, uptime, 404, concurrent requests, uptime increase
- Tests run without starting the server (httptest)
- Coverage is generated for CI (Codecov)

## Binary Size Comparison

One of Go's advantages is small binary size:

```bash
# Build and check size
go build -o devops-info-service main.go
ls -lh devops-info-service

# Results:
# Go binary: ~5.2 MB (with dependencies included)
# Python: ~23 MB (including venv and dependencies)
```

## Advantages Over Python Version

1. **Performance:**
   - Faster startup (milliseconds vs seconds)
   - Lower memory usage
   - Better concurrent request handling

2. **Deployment:**
   - Single binary (no virtual environment needed)
   - No dependency management in production
   - Easy cross-compilation

3. **Reliability:**
   - Static typing catches errors at compile time
   - No runtime dependency issues
   - Consistent behavior across environments

4. **Ideal for:**
   - Containerized deployments (smaller images)
   - Resource-constrained environments
   - High-traffic services

## Docker

The application is containerized using multi-stage builds for minimal image size.

### Building the Image

Build the Docker image using multi-stage build:

```bash
docker build -t <your-username>/devops-go-app:latest .
```

**Multi-stage build benefits:**
- Builder stage: Uses full Go toolchain (~300MB+)
- Runtime stage: Only contains compiled binary + alpine (~10-15MB total)
- 20x+ size reduction compared to including build tools

### Running the Container

Run the container with port mapping:

```bash
docker run -d -p 8080:8080 --name devops-go-app <your-username>/devops-go-app:latest
```

Access the application at `http://localhost:8080/`

### Pulling from Docker Hub

Pull and run the pre-built image:

```bash
docker pull <your-username>/devops-go-app:latest
docker run -d -p 8080:8080 <your-username>/devops-go-app:latest
```

### Docker Commands

```bash
# View logs
docker logs devops-go-app

# Stop container
docker stop devops-go-app

# Remove container
docker rm devops-go-app

# Check image size (should be ~10-15MB)
docker images <your-username>/devops-go-app
```

### Size Comparison

```
Python image:     226MB (slim base + Flask)
Go image:         ~12MB (alpine + static binary)
Reduction:        ~95% smaller
```

## Troubleshooting

### Port Already in Use

```bash
# Use different port
PORT=9090 ./devops-info-service

# Or for Docker:
docker run -d -p 9090:8080 <your-username>/devops-go-app:latest

# Or find process using the port
lsof -ti:8080 | xargs kill -9
```

### Docker Daemon Not Running

```bash
# Start Docker Desktop (macOS/Windows)
# Or start Docker daemon (Linux):
sudo systemctl start docker
```
