# DevOps Info Service (Go, Bonus)

## Overview

This directory contains a Go implementation of the **DevOps info service** with the same endpoints and JSON structure as the Python version:

- `GET /` — service, system, runtime, request and endpoints information
- `GET /health` — simple health check for monitoring and Kubernetes probes

## Prerequisites

- Go 1.22+ installed

## Build and Run

```bash
cd app_go

# Run directly
go run ./...

# Or build a binary
mkdir -p bin
go build -o bin/devops-info-service-go ./...

# Run the binary (default PORT=5002)
./bin/devops-info-service-go

# Custom port
PORT=8080 ./bin/devops-info-service-go
```

## API Endpoints

- `GET /`
  - Returns JSON with:
    - Service metadata (name, version, description, framework)
    - System info (hostname, platform, architecture, CPU count, Go version)
    - Runtime info (uptime in seconds and human readable, current time, timezone)
    - Request info (client IP, user agent, method, path)
    - List of available endpoints

- `GET /health`
  - Returns JSON with status, timestamp and uptime in seconds.

## Configuration

Configuration is done through environment variables:

| Variable | Default | Description                        |
|----------|---------|------------------------------------|
| `PORT`   | `5002`  | TCP port for HTTP server           |

The server listens on `0.0.0.0:PORT` by default.
