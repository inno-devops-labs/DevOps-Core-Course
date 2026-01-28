# DevOps Info Service (Go)

## Overview

This is a Go implementation of the **DevOps Info Service**, providing the same two endpoints as the Python version:

- `GET /` — service, system, runtime, request information, and a list of endpoints
- `GET /health` — simple health status with uptime

The service is designed for use in DevOps labs and multi-stage Docker builds.

## Prerequisites

- Go 1.22+ installed (`go version`)
- macOS / Linux / WSL (or any OS supported by Go)

## Project Structure

```text
app_go/
  ├── main.go
  ├── go.mod
  ├── README.md
  └── docs/
      ├── LAB01.md
      ├── GO.md
      └── screenshots/
```

## Configuration

Environment variables:

| Variable | Default  | Description                  |
|----------|----------|------------------------------|
| HOST     | 0.0.0.0  | Address to bind the service |
| PORT     | 8080     | Port to listen on           |

## Running the Service (development)

From the `app_go` directory:

```bash
go run main.go
```

With custom host/port:

```bash
HOST=127.0.0.1 PORT=9090 go run main.go
```

## Building the Binary

From the `app_go` directory:

```bash
go build -o devops-info-service-go
```

Run the binary:

```bash
./devops-info-service-go
```

Or with custom config:

```bash
HOST=127.0.0.1 PORT=8080 ./devops-info-service-go
```

## API Endpoints

### GET /

**Request:**

```bash
curl -s http://127.0.0.1:8080/ | python3 -m json.tool
```

Returns JSON with:

- `service` — name, version, description, framework (`net/http`)
- `system` — hostname, platform, architecture, CPU count, Go version
- `runtime` — uptime, current time (UTC), timezone
- `request` — client_ip, user_agent, method, path
- `endpoints` — list of available endpoints

### GET /health

**Request:**

```bash
curl -s http://127.0.0.1:8080/health | python3 -m json.tool
```

Returns JSON:

```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T13:17:37.656980Z",
  "uptime_seconds": 123
}
```

## Binary Size vs Python

To compare the Go binary size to the Python version:

1. **Build the Go binary:**

   ```bash
   cd app_go
   go build -o devops-info-service-go
   ls -lh devops-info-service-go
   ```

2. **Check approximate footprint of the Python app:**

   ```bash
   cd ../app_python
   du -sh venv
   ```

In a typical setup, the single Go binary is much smaller and self-contained compared to the full Python virtual environment, which makes Go attractive for small container images and multi-stage Docker builds.


