# Lab 01 Bonus — Go Implementation

## Implementation Overview

Go implementation of the DevOps Info Service with identical functionality to the Python version.

## Language Choice: Go

**Rationale:** Go provides single binary deployment, fast compilation, small binaries, and excellent concurrency. See [GO.md](GO.md) for detailed comparison.

## Implementation Details

### Standard Library Only

Uses only Go standard library:
- `net/http` - HTTP server and routing
- `encoding/json` - JSON serialization
- `runtime` - System information
- `os` - Environment variables
- `time` - Time operations

**Benefit:** Zero external dependencies, single binary deployment.

### HTTP Server

```go
func main() {
    host := os.Getenv("HOST")
    if host == "" {
        host = "0.0.0.0"
    }
    
    port := os.Getenv("PORT")
    if port == "" {
        port = "8080"
    }
    
    http.HandleFunc("/", mainHandler)
    http.HandleFunc("/health", healthHandler)
    
    addr := fmt.Sprintf("%s:%s", host, port)
    http.ListenAndServe(addr, nil)
}
```

### Main Endpoint

```go
func mainHandler(w http.ResponseWriter, r *http.Request) {
    if r.URL.Path != "/" {
        notFoundHandler(w, r)
        return
    }
    
    uptimeSeconds, uptimeHuman := getUptime()
    
    info := ServiceInfo{
        Service: Service{
            Name:        "devops-info-service",
            Version:     "1.0.0",
            Framework:   "Go net/http",
        },
        System: System{
            Hostname:     getHostname(),
            Platform:     runtime.GOOS,
            Architecture: runtime.GOARCH,
            CPUCount:     runtime.NumCPU(),
            GoVersion:    runtime.Version(),
        },
        // ... rest of fields
    }
    
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(info)
}
```

### Uptime Calculation

```go
var startTime = time.Now()

func getUptime() (int, string) {
    duration := time.Since(startTime)
    seconds := int(duration.Seconds())
    hours := seconds / 3600
    minutes := (seconds % 3600) / 60
    
    var human string
    if hours > 0 {
        human = fmt.Sprintf("%d hours, %d minutes", hours, minutes)
    } else {
        human = fmt.Sprintf("%d minutes", minutes)
    }
    
    return seconds, human
}
```

## API Documentation

### Endpoint: `GET /`

**Request:**
```bash
curl http://localhost:8080/
```

**Response:**

```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Go net/http"
  },
  "system": {
    "hostname": "MacBook-Pro--Egor.local",
    "platform": "darwin",
    "platform_version": "go1.25.6",
    "architecture": "arm64",
    "cpu_count": 11,
    "go_version": "go1.25.6"
  },
  "runtime": {
    "uptime_seconds": 41,
    "uptime_human": "0 minutes",
    "current_time": "2026-01-27T12:51:18.492136Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "[::1]:58274",
    "user_agent": "curl/8.7.1",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/health", "method": "GET", "description": "Health check"}
  ]
}
```

### Endpoint: `GET /health`

**Request:**
```bash
curl http://localhost:8080/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-27T12:51:25.44394Z",
  "uptime_seconds": 48
}
```

## Build & Deployment

### Build Commands

```bash
# Standard build
go build -o devops-info-service main.go

# Optimized build (smaller binary)
go build -ldflags="-s -w" -o devops-info-service main.go
```

### Binary Size Analysis

```bash
# Standard build
ls -lh devops-info-service
# Output: 7.6MB

# Optimized build
go build -ldflags="-s -w" -o devops-info-service main.go
ls -lh devops-info-service
# Output: 5.2MB

# Compare with Python
du -sh ../app_python/venv
# Output: 21MB
```

**Result:** Go binary is **4x smaller** than Python with venv (5.2MB vs 21MB).

### Running

```bash
# Run binary
./devops-info-service

# With custom port
PORT=3000 ./devops-info-service
```

## Performance Comparison

### Memory Usage

Real measurements on MacBook-Pro--Egor.local:

```bash
# Check memory usage
ps -o pid,rss,command -p <PID>

# Results:
# Go:     RSS = 7 MB
# Python: RSS = 35.5 MB
```

**Go uses 5x less memory (7 MB vs 35.5 MB).**

### Binary/Deployment Size

```bash
# Go binary (optimized)
ls -lh app_go/devops-info-service
# 5.2M

# Python with dependencies
du -sh app_python/venv
# 21M
```

**Go deployment is 4x smaller (5.2MB vs 21MB).**

### Startup Time

Measured startup time:

- **Go**: ~10-20ms (near instant)
- **Python**: ~300-500ms (Flask framework loading)

**Go starts 20-30x faster.**

### Request Handling

- **Go**: Handles each request in a separate goroutine (lightweight thread)
- **Python Flask**: Single-threaded by default

**Go's native concurrency provides better performance under load.**

## Best Practices Applied

### 1. Error Handling
```go
hostname, err := os.Hostname()
if err != nil {
    return "unknown"
}
```

### 2. Concurrency Ready
- HTTP server uses goroutines automatically
- Each request handled in separate goroutine

### 3. Standard Library First
- No external dependencies
- Uses proven stdlib packages

## Challenges & Solutions

### Challenge 1: No Built-in Framework

**Problem:** Python Flask provides routing, JSON, logging out of the box.

**Solution:** Standard library is sufficient. `net/http` is powerful and well-documented.

### Challenge 2: Verbose Error Handling

**Problem:** Go requires explicit error checking everywhere.

**Solution:** Catches errors at compile time - better than Python runtime surprises.

## Advantages Over Python Version

1. **Deployment** - Single binary (5.2MB), no venv, no dependencies
2. **Performance** - 20-30x faster startup, 5x less memory (7MB vs 35.5MB)
3. **Size** - 4x smaller (5.2MB vs 21MB for Python venv)
4. **Type Safety** - Compile-time error checking
5. **Concurrency** - Native goroutines for better request handling

## Disadvantages

1. **Development Speed** - More verbose than Python
2. **Dynamic Features** - No REPL, no dynamic typing flexibility
3. **Learning Curve** - Need to learn Go idioms

## Conclusion

The Go implementation successfully demonstrates:
- **Same functionality** as Python version
- **Better performance** in all metrics
- **Smaller footprint** for deployment
- **Production-ready** code with standard library only
