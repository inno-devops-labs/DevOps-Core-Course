# Lab 01 - Go Implementation

Go implementation of the DevOps Info Service (bonus task). Same functionality as Python version with compiled language advantages.

## Implementation

### Features
- Uses only Go standard library (no external dependencies)
- Single binary deployment (~6-8 MB)
- Fast compilation and execution
- Cross-platform support

### Code Structure
```go
package main

import (
    "encoding/json"
    "net/http"
    "os"
    "runtime"
    "time"
)

// Data structures for JSON responses
type ServiceInfo struct { ... }
type HealthResponse struct { ... }

// Global start time for uptime
var startTime = time.Now()

// Handlers
func mainHandler(w http.ResponseWriter, r *http.Request) { ... }
func healthHandler(w http.ResponseWriter, r *http.Request) { ... }
```

## Build

### Development
```bash
go build -o devops-info-service main.go
```
Size: ~8.5 MB

### Production (Optimized)
```bash
go build -ldflags="-s -w" -o devops-info-service main.go
```
Size: ~6.2 MB

### Cross-Platform
```bash
GOOS=linux GOARCH=amd64 go build -o devops-info-service-linux main.go
GOOS=windows GOARCH=amd64 go build -o devops-info-service.exe main.go
```

## API Endpoints

### `GET /`
Returns service and system information.

**Response:**
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "framework": "Go net/http"
  },
  "system": {
    "hostname": "my-laptop",
    "platform": "darwin",
    "architecture": "arm64",
    "cpu_count": 8
  },
  "runtime": {
    "uptime_seconds": 1234.56,
    "uptime_human": "0 hours, 20 minutes, 34 seconds"
  }
}
```

### `GET /health`
Health check endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-31T17:30:00.000Z",
  "uptime_seconds": 1234.56
}
```

## Comparison

| Aspect | Python | Go |
|--------|--------|-----|
| Dependencies | Flask (external) | None (stdlib) |
| Binary Size | N/A | ~6-8 MB |
| Deployment | Runtime + deps | Single binary |
| Startup Time | ~100-200ms | ~10-20ms |
| Memory Usage | ~30-50 MB | ~5-10 MB |

**Go Advantages:**
- Single binary deployment
- Faster execution
- Lower memory footprint
- No runtime dependencies
- Better for containers

## Testing

Screenshots available in `docs/screenshots/`:
1. Build process
2. Main endpoint response
3. Health check response

**Example:**
```bash
# Build
go build -o devops-info-service main.go

# Run
./devops-info-service

# Test
curl http://localhost:8080/ | jq
curl http://localhost:8080/health | jq
```

## Key Features

1. **System Information**: Uses `runtime` package for system info
2. **Uptime Calculation**: Tracks start time and formats human-readable
3. **Client IP Detection**: Handles proxy headers correctly
4. **Environment Variables**: Configurable via `PORT` env var
