# Lab 1 — DevOps Info Service: Go Implementation Report

**Language:** Go 1.21+  
**Framework:** Standard library `net/http`  
**Date:** January 28, 2026

---

## Overview

This document describes the Go implementation of the DevOps Info Service as a bonus task for Lab 1.

### Same Endpoints, Different Language

Both Flask (Python) and Go implementations expose:
- `GET /` - Complete service and system information
- `GET /health` - Health check for monitoring

### JSON Response Format

The response structure is identical to the Python version for consistency.

---

## Implementation

### Structure

The Go implementation is contained in a single `main.go` file with:
- Type definitions for all response structures
- HTTP handler functions
- Helper functions for system information
- Error handling middleware

### Key Features

1. **No External Dependencies**
   - Pure Go standard library
   - `net/http` for web server
   - `encoding/json` for serialization
   - `runtime` for system info

2. **Type Safety**
   - Structs define exact response format
   - JSON tags for serialization
   - Compile-time type checking

3. **Concurrency**
   - Goroutines handle requests naturally
   - Built-in for high-performance concurrent serving

4. **Performance**
   - Sub-millisecond startup
   - Single binary executable
   - Minimal memory footprint

### Build & Run

```bash
# Development (interpreted)
go run main.go

# Production (compiled)
go build -o devops-info-service main.go
./devops-info-service

# Cross-platform build
GOOS=linux GOARCH=amd64 go build -o devops-info-service main.go
```

---

## API Endpoints

### GET /

Same comprehensive response as Python version.

### GET /health

Same health check response as Python version.

---

## Configuration

Same environment variables as Python:
- `HOST` (default: 0.0.0.0)
- `PORT` (default: 8080)
- `DEBUG` (default: false)

---

## Testing

### Compilation Test

```bash
$ go build main.go
$ file main
main: Mach-O 64-bit executable arm64
$ ls -lh main
-rwxr-xr-x  1 user  staff  6.2M main
```

### Functional Test

```bash
$ PORT=3090 go run main.go &

# Test main endpoint
$ curl http://localhost:3090/ | jq .
# Or with Python3:
$ curl http://localhost:3090/ | python3 -m json.tool
# Or with Python:
$ curl http://localhost:3090/ | python -m json.tool

{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Go (http)"
  },
  "system": {
    "hostname": "pepegas-MacBook-Air.local",
    "platform": "darwin",
    "platform_version": "go1.24.4",
    "architecture": "arm64",
    "cpu_count": 10,
    "go_version": "1.24.4"
  },
  "runtime": {
    "uptime_seconds": 113,
    "uptime_human": "0 hours, 1 minute",
    "current_time": "2026-01-28T09:35:32.896325Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "[::1]",
    "user_agent": "curl/8.7.1",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {
      "path": "/",
      "method": "GET",
      "description": "Service and system information"
    },
    {
      "path": "/health",
      "method": "GET",
      "description": "Health check endpoint"
    }
  ]
}

# Test health endpoint
$ curl http://localhost:3090/health
{"status":"healthy","timestamp":"2026-01-28T09:34:28.009379Z","uptime_seconds":48}

# Pretty-printed health check
$ curl http://localhost:3090/health | python3 -m json.tool
{
    "status": "healthy",
    "timestamp": "2026-01-28T09:34:28.009379Z",
    "uptime_seconds": 48
}
```

**Note:** Replace `python3` with `python` if `python3` command is not available on your system.

---

## Advantages Summary

| Feature | Benefit |
|---------|---------|
| Single Binary | Easy deployment, no dependencies |
| Fast Startup | <100ms vs 500+ms for Python |
| Low Memory | 5-10 MB vs 50-100 MB for Python |
| Small Size | 6 MB vs 100+ MB with venv |
| Concurrent | Built-in goroutine support |
| DevOps Standard | Used by Docker, Kubernetes, etc. |

---

## Challenges & Solutions

### Challenge 1: 404 Error Handling

**Problem:** Go's `ServeMux` doesn't automatically handle undefined routes as 404.

**Solution:** 
```go
func handleIndex(w http.ResponseWriter, r *http.Request) {
    if r.URL.Path != "/" {
        http.NotFound(w, r)
        return
    }
    // ... handle request
}
```

### Challenge 2: Client IP Extraction

**Problem:** Need to extract client IP from `RemoteAddr` which includes port.

**Solution:**
```go
clientIP := r.RemoteAddr
if idx := strings.LastIndex(clientIP, ":"); idx != -1 {
    clientIP = clientIP[:idx]
}
```

### Challenge 3: System Information

**Problem:** Need to gather system info from `runtime` and `os` packages.

**Solution:** Used `runtime.GOOS`, `runtime.GOARCH`, `os.Hostname()`, `runtime.NumCPU()`.

---

## Files

- `main.go` - Complete application (single file)
- `go.mod` - Go module definition
- `README.md` - Setup and usage instructions
- `docs/GO.md` - Language justification and comparison
- `docs/LAB01.md` - This file

---

## Conclusion

The Go implementation provides a production-ready service identical in functionality to the Python version but with significant performance and deployment advantages. This serves as an excellent foundation for Lab 2's Docker containerization, where Go's single binary enables ultra-lightweight container images.

---

**Points:** +2.5 bonus
