# Lab 1 - DevOps Info Service: Web Application Initialisation (Go Implementation)

## Overview

This service provides detailed information about itself and its runtime environment. It exposes endpoints to retrieve system info, runtime status, and health check, forming a foundation for further DevOps tooling.

**Prerequisites**

- Go 1.25+ installed

## Installation

Clone the repo and navigate to the Go app folder:

```
git clone <your-repo-url>
cd app_go
```

Initialize and download dependencies (if needed):

```
go mod tidy
```

## Build

Build the binary executable:

```
go build -o devops-info-service.exe
# without .exe for non-windows systems
```

This produces `devops-info-service.exe` on Windows (developer does not know other systems).

## Running the Application

Run the binary with optional environment variables:

```
# Unix / Bash

HOST=0.0.0.0 PORT=8080 ./devops-info-service

# Windows PowerShell

$env:HOST="0.0.0.0"
$env:PORT="8080"
.\devops-info-service.exe
```

By default, the app listens on `0.0.0.0:8080` if no environment variables are set.

## API Endpoints

`GET /` - Service and system information (JSON)
`GET /health` - Health check status (JSON)

## JSON Structure

The JSON returned matches the Python version, including:

- Service metadata (name, version, description, framework)

- System info (hostname, platform, architecture, CPU count, Go version)

- Runtime info (uptime in seconds, human-readable uptime, current time, timezone)

- Request info (client IP, user agent, method, path)

- List of endpoints

## Framework Selection & Language Justification

- Chose Go for its simple concurrency model, small binaries, fast compile times, and widespread use in DevOps tooling.

- Go's standard library includes an efficient HTTP server which simplifies dependencies and deployment.

- The compiled binary enables easy multi-stage Docker builds.

## Best Practices Applied

- Clean Code Organization: Clear handlers and modular functions.

- Error Handling: Proper error checks and logging.

- Logging: Basic logs on server start and incoming requests helps with observing the app status.

- Configuration via Environment Variables: Enables flexible deployment without code changes.

- JSON Encoding: Uses Go's `encoding/json` for consistent API responses.

## API Documentation & Testing

Example `curl` requests:

```
curl -X GET "http://localhost:8080/" -H "accept: application/json"
curl -X GET "http://localhost:8080/health" -H "accept: application/json"
```

Example response snippet from `/`:

```
{
    "service": {
        "name": "devops-info-service",
        "version": "1.0.0",
        "description": "DevOps course info service",
        "framework": "Go net/http"
    },
    "system": {
        "hostname": "SfedBroPC",
        "platform": "windows",
        "architecture": "amd64",
        "cpu_count": 16,
        "go_version": "go1.25.6"
    },
    ...
}
```

## Challenges & Solutions

Managing JSON struct tags for proper response formatting.

Output differs with pythons os library(no adequate solution)

## Additional Notes

Go binaries are significantly smaller and start faster compared to Python interpreted mode.

### Comparing binary sizes

    2.61 Kb - python(4 Kb on my disk)
    7.98 Mb - go
