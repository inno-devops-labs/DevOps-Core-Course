![Go CI](https://github.com/mashfeii/DevOps-Core-Course/actions/workflows/go-ci.yml/badge.svg)
![Coverage](https://codecov.io/gh/mashfeii/DevOps-Core-Course/branch/master/graph/badge.svg?flag=go)

# devops info service (go)

a go web service that provides detailed information about itself and its runtime environment

## overview

this service exposes two endpoints that return json data about the system, service metadata, and health status

## prerequisites

- go 1.21 or higher

## building

```bash
# build the binary
go build -o devops-info-service main.go

# or run directly
go run main.go
```

## running the application

```bash
# default configuration (0.0.0.0:8080)
go run main.go

# or with binary
./devops-info-service

# custom port
PORT=3000 go run main.go

# custom host and port
HOST=127.0.0.1 PORT=3000 go run main.go
```

## api endpoints

### get /

returns comprehensive service and system information

**response example:**
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
    "uptime_seconds": 3600,
    "uptime_human": "1 hours, 0 minutes",
    "current_time": "2026-01-27T14:30:00Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1:52345",
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

### get /health

returns service health status for monitoring

**response example:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-27T14:30:00Z",
  "uptime_seconds": 3600
}
```

## configuration

| variable | default | description |
|----------|---------|-------------|
| HOST | 0.0.0.0 | server bind address |
| PORT | 8080 | server port |

## testing

### unit tests

```bash
# run tests
go test -v

# run tests with coverage
go test -coverprofile=coverage.out
go tool cover -func=coverage.out

# generate html coverage report
go tool cover -html=coverage.out -o coverage.html
```

### what's tested

- `GET /` endpoint: response structure, service info, system info, runtime info
- `GET /health` endpoint: status code, health status, uptime
- 404 handler: error response format
- helper functions: uptime calculation

### manual testing

```bash
# test main endpoint
curl http://localhost:8080/

# test health endpoint
curl http://localhost:8080/health

# pretty print json output
curl http://localhost:8080/ | python -m json.tool
```

## binary size comparison

the compiled go binary is significantly smaller than a python application with its dependencies:

| implementation | size |
|----------------|------|
| go binary | ~6-8 mb |
| python + flask | ~50+ mb (with venv) |

## docker

### building the image

```bash
docker build -t devops-info-service-go .
```

### running the container

```bash
docker run -p 8080:8080 devops-info-service-go
```

### multi-stage build

the dockerfile uses multi-stage build:
- stage 1 (builder): compiles the binary using golang:1.21-alpine
- stage 2 (runtime): copies only the binary to scratch image

this results in a final image of ~5-8 mb instead of ~300+ mb
