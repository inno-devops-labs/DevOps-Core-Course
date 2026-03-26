# DevOps Info Service (Go)

A production-ready web service providing detailed information about itself and its runtime environment. Written in Go for efficient resource usage and easy containerization.

## Overview

This is the Go implementation of the DevOps Info Service. It provides the same functionality as the Python version but with the benefits of a compiled language:

- **Single Binary**: No runtime dependencies
- **Small Footprint**: Minimal memory usage
- **Fast Startup**: Near-instant application start
- **Easy Deployment**: Just copy the binary

## Prerequisites

- **Go 1.21+** (tested with Go 1.21)

## Building the Application

### Standard Build

```bash
cd app_go
go build -o devops-info-service main.go
```

### Optimized Production Build

```bash
# Linux
CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o devops-info-service main.go

# Windows
set CGO_ENABLED=0
set GOOS=windows
go build -ldflags="-s -w" -o devops-info-service.exe main.go
```

Build flags explanation:
- `CGO_ENABLED=0`: Creates a static binary
- `-ldflags="-s -w"`: Strips debug info, reduces binary size

## Running the Application

### Using Go Run (Development)

```bash
go run main.go
```

### Using Compiled Binary

```bash
# Build first
go build -o devops-info-service main.go

# Run
./devops-info-service

# On Windows
devops-info-service.exe
```

### Custom Configuration

```bash
# Custom port
PORT=3000 ./devops-info-service

# Custom host and port
HOST=127.0.0.1 PORT=3000 ./devops-info-service
```

### Using PowerShell (Windows)

```powershell
$env:PORT="3000"; .\devops-info-service.exe
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
    "framework": "Go net/http"
  },
  "system": {
    "hostname": "my-laptop",
    "platform": "windows",
    "architecture": "amd64",
    "cpu_count": 8,
    "go_version": "go1.21.0"
  },
  "runtime": {
    "uptime_seconds": 120,
    "uptime_human": "2 minutes",
    "current_time": "2026-01-28T14:30:00.000000000Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1:54321",
    "user_agent": "curl/8.0.0",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/health", "method": "GET", "description": "Health check"},
    {"path": "/ready", "method": "GET", "description": "Readiness check"}
  ]
}
```

### `GET /health` - Health Check

Simple health endpoint for monitoring.

**Request:**
```bash
curl http://localhost:8080/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T14:30:00.000000000Z",
  "uptime_seconds": 120
}
```

### `GET /ready` - Readiness Check

Simple readiness endpoint for orchestrators such as Kubernetes.

**Request:**
```bash
curl http://localhost:8080/ready
```

**Response:**
```json
{
  "status": "ready",
  "timestamp": "2026-01-28T14:30:05.000000000Z"
}
```

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `HOST` | `0.0.0.0` | Host address to bind to |
| `PORT` | `8080` | Port number to listen on |

## Project Structure

```
app_go/
├── main.go              # Main application
├── go.mod               # Go module definition
├── Dockerfile           # Multi-stage container build
├── .dockerignore        # Docker build exclusions
├── README.md            # This file
└── docs/
    ├── LAB01.md         # Lab 1 submission
    ├── LAB02.md         # Lab 2 submission
    ├── GO.md            # Language justification
    └── screenshots/     # Proof of work
```

## Binary Size Comparison

| Version | Size |
|---------|------|
| Standard build | ~7 MB |
| Optimized (`-ldflags="-s -w"`) | ~5 MB |
| Python (with venv) | ~50+ MB |

The Go binary is self-contained with no external dependencies, making it ideal for containerization.

## Docker Usage

### Build Image Locally

```bash
docker build -t devops-info-service-go:latest .
```

### Run Container

```bash
docker run -d -p 8080:8080 --name devops-go-app devops-info-service-go:latest
```

Access the application at `http://localhost:8080`

### Pull from Docker Hub

```bash
docker pull Ravwvil/devops-info-service-go:latest
docker run -d -p 8080:8080 Ravwvil/devops-info-service-go:latest
```

### Image Size Advantage

The multi-stage build produces an image of only ~7-8 MB, compared to ~180-200 MB for Python.

Final image size: ~7 MB (compared to ~200 MB for Python)

## Development

### Code Style

This project follows standard Go conventions:
- `gofmt` for formatting
- Clear package organization
- Exported types documented
- Error handling

### Testing

```bash
go test ./...
```

## License

This project is part of the DevOps Engineering course.

## Author

DevOps Course Student
