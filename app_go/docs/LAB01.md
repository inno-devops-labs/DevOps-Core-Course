# Lab 01 - Go Implementation

Bonus task: DevOps Info Service in Go

## Overview

Compiled Go implementation of the Python service. Demonstrates advantages of compiled languages for production deployments.

## Framework Selection

**Chosen:** Go standard library (`net/http`)

**Why not frameworks (Gin, Echo)?**
- Zero dependencies
- Standard library is stable and production-ready
- Simple 2-endpoint service doesn't need frameworks
- Used by Kubernetes, Docker, Prometheus

## Best Practices Applied

### 1. Structured Logging
```go
log.SetFlags(log.LstdFlags | log.Lshortfile)
log.Printf("Request: %s %s from %s", r.Method, r.URL.Path, ip)
```

### 2. Explicit Error Handling
```go
if err := encoder.Encode(info); err != nil {
    log.Printf("Error: %v", err)
    http.Error(w, "Internal Server Error", 500)
}
```

### 3. Environment Configuration
```go
host := os.Getenv("HOST")
if host == "" {
    host = "0.0.0.0"
}
```

### 4. Type Safety
```go
type ServiceInfo struct {
    Service   Service   `json:"service"`
    System    System    `json:"system"`
    Runtime   Runtime   `json:"runtime"`
}
```

## API Documentation

### GET /

Same structure as Python version with `"framework": "Go net/http"`.

```bash
curl http://localhost:8000/
```

### GET /health

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-26T07:30:00Z",
  "uptime_seconds": 42
}
```

## Building and Running

### Development
```bash
go run main.go
PORT=8080 go run main.go
```

### Production
```bash
# Build optimized
go build -ldflags="-s -w" -o devops-info-service main.go

# Run
./devops-info-service

# Check size
ls -lh devops-info-service
```

### Cross-Compile
```bash
GOOS=linux GOARCH=amd64 go build -o service-linux main.go
GOOS=windows GOARCH=amd64 go build -o service.exe main.go
```

## Binary Size Comparison

```
Go:     7.2 MB  (single binary, no dependencies)
Python: ~80 MB  (runtime + packages)
Savings: 91% smaller!
```


## Testing Evidence

Screenshots in `docs/screenshots/`:
- `01-go-main-endpoint.png` - GET / response
- `02-go-health-check.png` - GET /health response  
- `03-go-build-output.png` - Build + binary size
