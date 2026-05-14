# DevOps Info Service (Go)

[![CI/CD Pipeline](https://github.com/pav0rkmert/DevOps-Core-Course/workflows/Go%20CI%2FCD%20Pipeline/badge.svg)](https://github.com/pav0rkmert/DevOps-Core-Course/actions)
[![Coverage](https://codecov.io/gh/pav0rkmert/DevOps-Core-Course/branch/main/graph/badge.svg?flag=go)](https://codecov.io/gh/pav0rkmert/DevOps-Core-Course)

A Go implementation of the DevOps Info Service that provides system information and health status endpoints. This implementation demonstrates the benefits of compiled languages for containerized microservices.

## Overview

This is the Go version of the DevOps Info Service, providing the same REST API endpoints as the Python version:
- Service and system information
- Health check for monitoring and Kubernetes probes
- Ready-to-deploy Fly.io configuration in `fly.toml`

## Prerequisites

- Go 1.21 or higher

## Building

### Development Build

```bash
go build -o devops-info-service main.go
```

### Production Build (Optimized)

```bash
CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags="-s -w" -o devops-info-service main.go
```

The `-ldflags="-s -w"` flags strip debug information for a smaller binary.

## Running

### Run Directly

```bash
go run main.go
```

### Run Compiled Binary

```bash
./devops-info-service
```

The service will start on `http://0.0.0.0:8080` by default.

### Custom Configuration

```bash
# Custom port
PORT=3000 ./devops-info-service

# Custom host and port
HOST=127.0.0.1 PORT=9000 ./devops-info-service
```

## API Endpoints

### `GET /` — Service Information

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
    "platform": "darwin",
    "architecture": "arm64",
    "cpu_count": 8,
    "go_version": "go1.21.0"
  },
  "runtime": {
    "uptime_seconds": 120,
    "uptime_human": "0 hours, 2 minutes",
    "current_time": "2026-01-28T12:00:00Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1:54321",
    "user_agent": "curl/8.1.2",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/health", "method": "GET", "description": "Health check"}
  ]
}
```

### `GET /health` — Health Check

**Request:**
```bash
curl http://localhost:8080/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T12:00:00Z",
  "uptime_seconds": 120
}
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Host address to bind |
| `PORT` | `8080` | Port number |

## Binary Size Comparison

| Implementation | Binary/Package Size | Startup Time |
|----------------|---------------------|--------------|
| Go (optimized) | ~6-8 MB | <50ms |
| Python + Flask | ~50+ MB (with venv) | ~500ms |

Go produces a single static binary with no external dependencies, making it ideal for containerization:
- Smaller Docker images (can use `scratch` or `alpine` base)
- Faster container startup
- No runtime dependencies

## Project Structure

```
app_go/
├── main.go         # Main application
├── main_test.go    # Unit tests
├── go.mod          # Go module definition
├── .gitignore      # Git ignore rules
├── README.md       # This file
└── docs/
    ├── LAB01.md   # Lab 1 submission
    ├── LAB02.md   # Lab 2 submission
    └── GO.md      # Language justification
```

## Docker (Lab 2 Preview)

The Go implementation enables efficient multi-stage Docker builds:

```dockerfile
# Build stage
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY . .
RUN CGO_ENABLED=0 go build -ldflags="-s -w" -o devops-info-service

# Runtime stage
FROM scratch
COPY --from=builder /app/devops-info-service /
EXPOSE 8080
ENTRYPOINT ["/devops-info-service"]
```

Final image size: ~8-10 MB (compared to ~150+ MB for Python with dependencies).

## Development

### Code Style

This project follows standard Go conventions:
- `gofmt` for formatting
- `golint` for linting
- Clear package structure

```bash
# Format code
gofmt -w .

# Run linter
golint ./...
```

### Testing

```bash
# Run all tests
go test ./...

# Run tests with coverage
go test -v -coverprofile=coverage.out ./...

# View coverage report
go tool cover -html=coverage.out

# Run tests with coverage percentage
go test -cover ./...
```

### Test Coverage

The project uses Go's built-in coverage tools. Coverage reports are automatically uploaded to Codecov on each CI run.

**Current Coverage:** Tests cover main endpoints (`GET /`, `GET /health`), error handling, and helper functions.

**Coverage Target:** Aim for 70%+ coverage of critical paths (endpoints, error handling).

## License

This project is part of the DevOps course curriculum.
