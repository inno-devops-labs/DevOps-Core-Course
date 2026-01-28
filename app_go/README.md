# DevOps Info Service (Go)

A lightweight web service providing system and runtime information, built with Go's standard library.

## Prerequisites

- Go 1.21 or higher

## Installation

No external dependencies required - uses only Go standard library.

```bash
go mod download
```

## Building

```bash
# Build for current platform
go build -o devops-service main.go

# Build for Linux (cross-compile from any OS)
GOOS=linux GOARCH=amd64 go build -o devops-service-linux main.go

# Build for Windows
GOOS=windows GOARCH=amd64 go build -o devops-service.exe main.go
```

## Running

```bash
# Run directly without building
go run main.go

# Or use the compiled binary
./devops-service

# Custom port configuration
PORT=3000 ./devops-service
```

## API Endpoints

### GET /
Returns comprehensive service and system information including:
- Service metadata (name, version, framework)
- System details (hostname, platform, architecture, CPU count, Go version)
- Runtime metrics (uptime, current time)
- Request information (client IP, user agent, method, path)

### GET /health
Health check endpoint returning service status and uptime.
Used for monitoring and Kubernetes liveness/readiness probes.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8080` | Server listening port |

## Binary Size Comparison

```bash
# Go binary (statically linked, no dependencies)
$ ls -lh devops-service
-rwxr-xr-x  7.2M  devops-service

# Python container (requires interpreter + dependencies)
$ docker images python:3.11-slim
python:3.11-slim  ~120 MB
```

Go produces a self-contained executable that is **~17x smaller** than a Python container image.

## Testing

```bash
# Start the service
./devops-service

# In another terminal
curl http://localhost:8080/ | jq
curl http://localhost:8080/health
```