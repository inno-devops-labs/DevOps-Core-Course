# DevOps Info Service (Go Version)

A production-ready web service providing detailed information about itself and its runtime environment. Built with Go `net/http` for high performance and simplicity.

## Overview

The DevOps Info Service is a Go-based web application that reports comprehensive system information, runtime statistics, and service metadata. This service can be used as a foundation for monitoring tools in a DevOps environment.

**Features:**
- System information (hostname, platform, architecture, CPU count, Go version)
- Runtime statistics (uptime, current time, timezone)
- Request metadata (client IP, user agent, method, path)
- Health check endpoint for monitoring

## Prerequisites

- **Go 1.21+** (recommended)
- Operating System: Windows/macOS/Linux


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

## API Endpoints

### `GET /`

Returns comprehensive service and system information.


- service: service metadata (name, version, description, framework)

- system: information about system (hostname, platform, architecture, CPU count, Python version)

- runtime: runtime metrics (uptime, current time, timezone)

- request: details of request (client IP, user agent, method, path)

- endpoints: available API endpoints

**Response Example:**
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
    "platform": "linux",
    "platform_version": "linux amd64",
    "architecture": "amd64",
    "cpu_count": 8,
    "go_version": "go1.21.1"
  },
  "runtime": {
    "uptime_seconds": 3600,
    "uptime_human": "1 hours, 0 minutes",
    "current_time": "2026-01-28T14:30:00Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1:54321",
    "user_agent": "curl/7.81.0",
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

**Testing:**
```bash
curl http://localhost:5000/
```

### `GET /health`

Simple health check endpoint for monitoring and Kubernetes liveness/readiness probes.

**Response Example:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T14:30:00.000000+00:00",
  "uptime_seconds": 3600
}
```

**HTTP Status:** 200 OK

**Testing:**
```bash
curl http://localhost:5000/health
```

## Configuration

The application can be configured using the following environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Host address to bind the server |
| `PORT` | `5000` | Port number to listen on |
| `DEBUG` | `False` | Enable debug mode  |



## Development

### Project Structure

```
app_go/  (or app_rust, app_java, etc.)
├── main.go
├── go.mod
├── README.md
└── docs/
    ├── LAB01.md              # Implementation details
    ├── GO.md                 # Language justification
    └── screenshots/
```


## Testing

Test the endpoints using curl, HTTPie, or any HTTP client:

```bash
# Main endpoint
curl http://localhost:5000/

# Health endpoint
curl http://localhost:5000/health

# Formatted JSON
curl -s http://localhost:5000/ | python -m json.tool
```



## Comparison of performance
### Memory Usage
**Go version:**
```bash
PS D:\PycharmProjects\DevOps-Core-Course\app_go> go build -o devops-info-service.exe main.go
PS D:\PycharmProjects\DevOps-Core-Course\app_go> Get-Item .\devops-info-service.exe | Select-Object Name, Length

Name                     Length
----                     ------
devops-info-service.exe 8380416


PS D:\PycharmProjects\DevOps-Core-Course\app_go> (Get-Item .\devops-info-service.exe).Length / 1MB
7,9921875
PS D:\PycharmProjects\DevOps-Core-Course\app_go>

```
**Python version:**
```bash
(venv) PS D:\PycharmProjects\DevOps-Core-Course\app_python> Get-ChildItem .\venv -Recurse | Measure-Object -Property Length -Sum


Count    : 1821
Average  :
Sum      : 30915401
Maximum  :
Minimum  :
Property : Length



(venv) PS D:\PycharmProjects\DevOps-Core-Course\app_python> ( (Get-ChildItem .\venv -Recurse | Measure-Object -Property Length -Sum).Sum ) / 1MB
29,4832239151001
(venv) PS D:\PycharmProjects\DevOps-Core-Course\app_python>
```
**Go uses significantly less memory (7,9 MB vs 29,5 MB).**

## Troubleshooting

### Port Already in Use

```bash
# Use another port
$env:PORT="9090"
.\devops-info-service.exe

# Or find process using the port
lsof -ti:8080 | xargs kill -9
```