# DevOps Info Service (Go)
## Overview
A Go-based web service designed to furnish details about itself and its operational environment. This compiled version of the service is optimized for containerization and multi-stage Docker builds, offering improved performance and smaller deployment footprints compared to interpreted languages.

## Prerequisites
- Go 1.21 or higher
- Git (for dependency management)

## Installation
1. Clone repository:

```bash
# Clone the project
git clone https://github.com/s3rap1s/DevOps-Core-Course.git
cd DevOps-Core-Course/app_go

# Download dependencies
go mod download

# Build the application
go build -o devops-info-service
```

## Running the Application
```bash
# Default configuration
./devops-info-service

# With custom port
PORT=8080 ./devops-info-service

# With custom port and host
HOST=127.0.0.1 PORT=3000 ./devops-info-service

# Run directly without building
go run main.go
Building for Different Platforms
bash
# Build for current platform
go build -o devops-info-service
```

## API Endpoints
### GET /
Return comprehensive service and system information:

```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Go"
  },
  "system": {
    "hostname": "my-laptop",
    "platform": "linux",
    "platform_version": "Linux Kernel",
    "architecture": "amd64",
    "cpu_count": 8,
    "go_version": "go1.21.4"
  },
  "runtime": {
    "uptime_seconds": 3600,
    "uptime_human": "1 hour, 0 minutes",
    "current_time": "2026-01-07T14:30:00.000Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1:12345",
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

### GET /health
Simple health endpoint for monitoring:

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T14:30:00.000Z",
  "uptime_seconds": 3600
}
```

## Configuration
| Variable | Default   | Description                  |
| -------- | --------- | ---------------------------- |
| `HOST`   | `0.0.0.0` | Network interface to bind    |
| `PORT`   | `5000`    | Port to listen on            |