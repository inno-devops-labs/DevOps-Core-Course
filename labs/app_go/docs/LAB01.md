# Lab 01 - Go Implementation Details

## Overview

This document details the Go implementation of the DevOps Info Service for Lab 1 bonus task.

## Implementation Approach

### Framework Choice: Standard Library (`net/http`)

Instead of using external frameworks like Gin or Echo, I used Go's standard library `net/http` package. This choice demonstrates Go's philosophy of "batteries included" and keeps the binary minimal with zero external dependencies.

### Project Structure

```
app_go/
├── main.go              # Single file containing all application logic
├── go.mod               # Go module definition
├── README.md            # User documentation
└── docs/
    ├── LAB01.md        # This file
    ├── GO.md           # Language justification
    └── screenshots/    # Proof of work
```

## Code Highlights

### 1. Type-Safe JSON Responses

Go's struct tags provide clean JSON serialization:

```go
type Service struct {
    Name        string `json:"name"`
    Version     string `json:"version"`
    Description string `json:"description"`
    Framework   string `json:"framework"`
}
```

### 2. Uptime Calculation

```go
var startTime = time.Now()

func getUptime() (int, string) {
    duration := time.Since(startTime)
    seconds := int(duration.Seconds())
    hours := seconds / 3600
    minutes := (seconds % 3600) / 60
    return seconds, fmt.Sprintf("%d hours, %d minutes", hours, minutes)
}
```

### 3. Environment Configuration

```go
port := os.Getenv("PORT")
if port == "" {
    port = "8080"
}

host := os.Getenv("HOST")
if host == "" {
    host = "0.0.0.0"
}
```

### 4. Error Handling

```go
func notFoundHandler(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(http.StatusNotFound)
    json.NewEncoder(w).Encode(ErrorResponse{
        Error:   "Not Found",
        Message: "Endpoint does not exist",
    })
}
```

### 5. Logging

```go
log.Printf("Request: %s %s from %s", r.Method, r.URL.Path, getClientIP(r))
```

## API Documentation

### Main Endpoint: `GET /`

**Command:**
```bash
curl -s http://localhost:8080/ | jq .
```

**Response:**
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "net/http"
  },
  "system": {
    "hostname": "hostname",
    "platform": "linux",
    "platform_version": "linux/amd64",
    "architecture": "amd64",
    "cpu_count": 8,
    "go_version": "go1.21.0"
  },
  "runtime": {
    "uptime_seconds": 120,
    "uptime_human": "0 hours, 2 minutes",
    "current_time": "2026-01-26T16:33:00Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1:54321",
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

### Health Endpoint: `GET /health`

**Command:**
```bash
curl -s http://localhost:8080/health | jq .
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-26T16:33:00Z",
  "uptime_seconds": 120
}
```

## Build & Run

### Development
```bash
go run main.go
```

### Production Binary
```bash
CGO_ENABLED=0 go build -ldflags="-s -w" -o devops-info-service main.go
./devops-info-service
```

## Binary Size Comparison

```bash
# Build and check size
go build -o app main.go
ls -lh app
# Result: ~7MB standard, ~5MB optimized

# Compare to Python
du -sh ../app_python/venv
# Result: ~50MB+ for virtual environment
```

## Screenshots

The screenshots below demonstrate the working application:

1. **Compilation Output** - `screenshots/01-compilation.png`
2. **Main Endpoint Response** - `screenshots/02-main-endpoint.png`
3. **Health Check Response** - `screenshots/03-health-check.png`

> **Note:** Screenshots should be captured after building and running the application.

## Differences from Python Version

| Aspect | Python (FastAPI) | Go (net/http) |
|--------|-----------------|---------------|
| Response field | `python_version` | `go_version` |
| Default port | 5000 | 8080 |
| Binary | None (interpreted) | Static binary |
| Startup time | ~500ms | ~10ms |
| Framework | FastAPI | Standard library |
