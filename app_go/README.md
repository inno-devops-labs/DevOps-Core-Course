## DevOps Info Service (Go implementation)

This is the **compiled-language (Go)** implementation of the DevOps Info Service.  
It exposes the same two endpoints as the Python version:

- `GET /` — service, system, runtime and request information
- `GET /health` — lightweight health check for monitoring and probes

The service is implemented with the Go standard library (`net/http`) for minimal
dependencies and fast, small binaries.

### Overview

The Go service returns:

- **Service metadata**: name, version, description, framework (`Go net/http`)
- **System info**: hostname, OS, architecture, CPU count, Go version
- **Runtime info**: uptime in seconds and human-readable format, current UTC time
- **Request info**: client IP, user agent, HTTP method, request path
- **Endpoints list**: description of available HTTP endpoints

The `/health` endpoint returns a compact JSON payload with status, timestamp and
uptime in seconds.

### Prerequisites

- **Go 1.22+** (matches `go.mod`)
- Git (optional, for cloning repository)

### Project structure

```text
app_go/
├── main.go       # Main Go application (HTTP server)
├── go.mod        # Go module definition
├── README.md     # This file
└── docs/
    ├── LAB01.md  # Lab report for Go version
    ├── GO.md     # Language justification (why Go)
    └── screenshots/
        ├── 01-main-endpoint-go.png
        ├── 02-health-check-go.png
        └── 03-go-build-and-run.png
```

## Building

```bash
cd app_go
go build -o devops-info-service.exe
```

## Running

```bash
.\devops-info-service.exe
```
- Starts the service on port 5000 by default
- Access endpoints at:
    - http://localhost:5000/ — main service info
    - http://localhost:5000/health — health check

#### Custom Port
To run on a different port (e.g., 8090):
```bash
$env:PORT="8090"
.\devops-info-service.exe
```

#### Running Without Building

Go can run the service directly from source without building a binary:
```bash
go run main.go
```
### API endpoints

#### `GET /`

Returns full service, system, runtime and request information.

**Example request:**

```bash
curl http://localhost:5000/
```

**Example response (shape):**

```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Go net/http"
  },
  "system": {
    "hostname": "my-machine",
    "platform": "linux",
    "platform_version": "linux amd64",
    "architecture": "amd64",
    "cpu_count": 8,
    "go_version": "go1.22.0"
  },
  "runtime": {
    "uptime_seconds": 3600,
    "uptime_human": "1 hours, 0 minutes",
    "current_time": "2026-01-28T14:30:00Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1:51234",
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

#### `GET /health`

Lightweight health-check endpoint.

**Example request:**

```bash
curl http://localhost:5000/health
```

**Example response:**

```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T14:30:00Z",
  "uptime_seconds": 3600
}
```

### Configuration

The Go service is configured via environment variables:

| Variable | Default | Description                        |
|----------|---------|------------------------------------|
| `HOST` | `0.0.0.0` | Host address to bind |
| `PORT`   | `5000`  | TCP port to listen on (string)    |



### Testing

After starting the server:

```bash
# Main endpoint
curl http://localhost:5000/

# Health endpoint
curl http://localhost:5000/health

# Formatted JSON
curl -s http://localhost:5000/ | python -m json.tool
```

You can also open these URLs in a browser:

- `http://localhost:5000/`
- `http://localhost:5000/health`

### Notes for screenshots 

For the bonus task, screenshots were captered and saved into `app_go/docs/screenshots/`
