# Lab 01 Bonus - DevOps Info Service

## Implementation Overview

This document describes the Go implementation of the DevOps Info Service, completed as the bonus task for Lab 01. The Go version provides the same functionality as the Python version but with improved performance, smaller deployment size, and zero runtime dependencies.

## Language Choice

See [GO.md](GO.md) for detailed justification of why Go was selected for this implementation.

**Key Reasons:**
- Single binary deployment (no dependencies)
- Fast startup time (~milliseconds)
- Low memory footprint (~8 MB)
- Native to DevOps ecosystem (Docker, Kubernetes written in Go)
- Perfect for containerization (Lab 2)

## Implementation Details

### Architecture

The Go implementation uses:
- **Standard library only** - No external dependencies
- **net/http package** - Built-in HTTP server
- **Structured types** - Go structs for JSON serialization
- **Modular functions** - Separation of concerns

### Code Structure

```go
// Data structures define API responses
type ServiceInfo struct {
    Service   Service
    System    System
    Runtime   Runtime
    Request   Request
    Endpoints []Endpoint
}

// Helper functions collect information
func getSystemInfo() System { }
func getUptime() (int, string) { }
func getRequestInfo(r *http.Request) Request { }

// HTTP handlers serve endpoints
func mainHandler(w http.ResponseWriter, r *http.Request) { }
func healthHandler(w http.ResponseWriter, r *http.Request) { }
```

### Key Features Implemented

**1. Type Safety**
```go
// Compile-time type checking
type System struct {
    Hostname     string `json:"hostname"`
    Platform     string `json:"platform"`
    Architecture string `json:"architecture"`
    CPUCount     int    `json:"cpu_count"`
    GoVersion    string `json:"go_version"`
}
```

**2. Error Handling**
```go
// Explicit error handling
hostname, err := os.Hostname()
if err != nil {
    hostname = "unknown"
    log.Printf("Error getting hostname: %v", err)
}
```

**3. Configuration**
```go
// Environment variables with defaults
host := os.Getenv("HOST")
if host == "" {
    host = "0.0.0.0"
}
```

**4. Logging**
```go
// Built-in logging
log.Printf("Request: %s %s from %s", r.Method, r.URL.Path, r.RemoteAddr)
```

**5. JSON Serialization**
```go
// Automatic JSON encoding with struct tags
w.Header().Set("Content-Type", "application/json")
json.NewEncoder(w).Encode(info)
```

## API Endpoints

### GET /

Returns comprehensive service and system information.

**Testing Command:**
```bash
curl http://localhost:8080/
```

**Response Structure:**
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Go net/http"
  },
  "system": {
    "hostname": "MacBook-Pro.local",
    "platform": "darwin",
    "platform_version": "darwin arm64",
    "architecture": "arm64",
    "cpu_count": 8,
    "go_version": "go1.21.0"
  },
  "runtime": {
    "uptime_seconds": 45,
    "uptime_human": "45 seconds",
    "current_time": "2026-01-27T12:00:00.000000000Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1:52334",
    "user_agent": "curl/8.7.1",
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

### GET /health

Health check endpoint for monitoring.

**Testing Command:**
```bash
curl http://localhost:8080/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-27T12:00:00.000000000Z",
  "uptime_seconds": 45
}
```

## Build and Run

### Build Process

```bash
# Build for current platform
go build -o devops-info-service main.go

# Build with optimizations (smaller binary)
go build -ldflags="-s -w" -o devops-info-service main.go
```

### Running

```bash
# Run directly with Go
go run main.go

# Or run compiled binary
./devops-info-service

# With custom configuration
PORT=3000 ./devops-info-service
```

### Testing

```bash
# Test main endpoint
curl http://localhost:8080/

# Test health endpoint
curl http://localhost:8080/health

# Pretty-print JSON
curl http://localhost:8080/ | python -m json.tool
```

## Performance Comparison

Comparing Go vs Python implementations:

### Binary Size

```bash
# Go binary (with dependencies included)
ls -lh devops-info-service
# Result: 5.2 MB

# Python
du -sh app_python/
# Result: ~23 MB (including venv and dependencies)
```

Ratio: Go is ~4x smaller

## Advantages Demonstrated

**1. Deployment Simplicity**
- Go: binary size is 5.2 MB
- Python: binary size is 23 MB

**2. Cross-Platform**
```bash
# Build for 5 platforms in seconds
GOOS=linux GOARCH=amd64 go build
GOOS=linux GOARCH=arm64 go build
GOOS=darwin GOARCH=amd64 go build
GOOS=darwin GOARCH=arm64 go build
GOOS=windows GOARCH=amd64 go build
```

**3. No Dependencies**
- Go: Zero external dependencies
- Python: Flask, Werkzeug, and their dependencies

## Best Practices Applied

### 1. Clean Code Organization

```go
// Grouped by purpose
// - Type definitions at top
// - Helper functions in middle
// - HTTP handlers
// - Main function at bottom
```

### 2. Error Handling

```go
// All errors handled explicitly
if err := json.NewEncoder(w).Encode(info); err != nil {
    log.Printf("Error encoding JSON: %v", err)
}
```

### 3. Documentation

```go
// Comments explain function purpose
// getSystemInfo collects system information
func getSystemInfo() System {
    // Implementation
}
```

## Challenges and Solutions

### Challenge 1: JSON Field Naming

**Problem:** Go uses PascalCase for exported fields, but JSON should use snake_case.

**Solution:** Use struct tags

```go
type System struct {
    CPUCount int `json:"cpu_count"`  // Exports as "cpu_count" in JSON
}
```

### Challenge 2: Uptime Formatting

**Problem:** Same logic as Python, but in Go syntax.

**Solution:** Calculate and format with conditionals

```go
if hours > 0 {
    human = fmt.Sprintf("%d hours, %d minutes", hours, minutes)
} else if minutes > 0 {
    human = fmt.Sprintf("%d minutes", minutes)
} else {
    human = fmt.Sprintf("%d seconds", seconds)
}
```

## Testing Evidence

Screenshots in `docs/screenshots/` demonstrate:

1. **Successful compilation** - Go build output
2. **Running service** - Server startup logs
3. **Main endpoint response** - Complete JSON from GET /
4. **Health check response** - JSON from GET /health
5. **Binary size comparison** - File sizes of Go vs Python

### Terminal Output

```
2026/01/27 21:45:47 Starting DevOps Info Service...
2026/01/27 21:45:47 Host: 0.0.0.0, Port: 8080
2026/01/27 21:45:47 Visit: http://0.0.0.0:8080/
2026/01/27 21:45:47 Server starting on 0.0.0.0:8080
2026/01/27 21:54:48 Request: GET / from [::1]:62866
2026/01/27 21:59:02 Health check from [::1]:63278
2026/01/27 22:08:40 Request: GET / from [::1]:64157
2026/01/27 22:09:47 Request: GET / from [::1]:64262
```