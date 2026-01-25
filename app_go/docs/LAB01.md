# Lab 1 (Bonus) — DevOps Info Service in Go

## 1. Language / Framework Selection

### Choice
I implemented the bonus service in **Go** using the standard library **net/http** package.

### Why Go?
- **Compiled binary**: produces a single executable (useful for multi-stage Docker builds).
- **Fast startup and low overhead**: good for microservices.
- **Standard library is enough**: `net/http` covers routing and HTTP server without external frameworks.
- **Great DevOps fit**: simple deployment, small runtime requirements.

### Comparison with Alternatives

| Criteria | Go (net/http) (chosen) | Rust | Java (Spring Boot) | C# (ASP.NET Core) |
|---------|--------------------------|------|---------------------|-------------------|
| Build artifact | Single binary | Single binary | JVM app + deps | .NET app + deps |
| Startup time | Fast | Fast | Usually slower | Medium |
| Runtime deps | None | None | JVM required | .NET runtime |
| HTTP stack | stdlib | frameworks (Axum/Actix) | Spring ecosystem | ASP.NET stack |
| Complexity | Low | Medium–high | Medium | Medium |
| Best fit for this lab | Excellent | Good | Overkill | Good |

---

## 2. Best Practices Applied

### 2.1 Clean Code Organization
- Clear data models (`ServiceInfo`, `Service`, `System`, `RuntimeInfo`, `RequestInfo`, `Endpoint`).
- Helper functions for concerns separation:
  - `runtimeInfo()`, `requestInfo()`, `uptime()`, `isoUTCNow()`, `clientIP()`, `writeJSON()`.

### 2.2 Configuration via Environment Variables
The service is configurable via environment variables:
- `HOST` (default `0.0.0.0`)
- `PORT` (default `8080`)
- `DEBUG` (default `false`)

Implementation uses a simple helper:
```go
func getenv(key, def string) string {
    v := os.Getenv(key)
    if v == "" {
        return def
    }
    return v
}
```

### 2.3 Logging Middleware
Request logging is implemented as middleware:
```go
func withLogging(logger *log.Logger) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            start := time.Now()
            next.ServeHTTP(w, r)
            logger.Printf("%s %s (%s) from %s in %s",
                r.Method, r.URL.Path, r.Proto, r.RemoteAddr, time.Since(start))
        })
    }
}
```

### 2.4 Error Handling
#### 404 Not Found
Unknown endpoints return a consistent JSON error:
```json
{
  "error": "Not Found",
  "message": "Endpoint does not exist"
}
```
This is implemented via a wrapper that enforces valid paths:
```go
func withNotFound(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        if r.URL.Path != "/" && r.URL.Path != "/health" {
            writeJSON(w, http.StatusNotFound, ErrorResponse{
                Error: "Not Found",
                Message: "Endpoint does not exist",
            })
            return
        }
        next.ServeHTTP(w, r)
    })
}
```
#### 500 Internal Server Error (panic recovery)
A recover middleware prevents crashes and returns a safe JSON response:
```go
func withRecover(logger *log.Logger) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            defer func() {
                if rec := recover(); rec != nil {
                    logger.Printf("panic recovered: %v", rec)
                    writeJSON(w, http.StatusInternalServerError, ErrorResponse{
                        Error: "Internal Server Error",
                        Message: "An unexpected error occurred",
                    })
                }
            }()
            next.ServeHTTP(w, r)
        })
    }
}
```
### 2.5 Production-Friendly HTTP Server Settings
The service uses `http.Server` with timeouts:
```go
srv := &http.Server{
    Addr: addr,
    Handler: handler,
    ReadHeaderTimeout: 5 * time.Second,
}
```
## 3. API Documentation
### 3.1 GET / — Service and System Information
**Description**: Returns service metadata, system info, runtime info, request info, and available endpoints.

**Request**:
```bash
curl -i http://127.0.0.1:8080/
```
**Response (200 OK) example**:
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Go net/http"
  },
  "system": {
    "hostname": "DESKTOP-KUN1CI4",
    "platform": "windows",
    "platform_version": "unknown",
    "architecture": "amd64",
    "cpu_count": 8,
    "go_version": "go1.25.6"
  },
  "runtime": {
    "uptime_seconds": 6,
    "uptime_human": "0 hours, 0 minutes",
    "current_time": "2026-01-25T17:17:32.248Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "::1",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0",
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
### 3.2 GET /health — Health Check
**Description**: Description: Simple health endpoint used for monitoring and probes.

**Request**:
```bash
curl -i http://127.0.0.1:8080/health
```
**Response (200 OK) example**:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-25T17:19:02.582Z",
  "uptime_seconds": 96
}
```
### 3.3 404 Behavior
**Request**:
```bash
curl -i http://127.0.0.1:8080/does-not-exist
```
**Response (404 Not Found)**:
```json
{
  "error": "Not Found",
  "message": "Endpoint does not exist"
}
```

## 4. Build & Run Instructions
### 4.1 Run locally (no build)
```bash
go run main.go
```
### 4.2 Build binary
```bash
go build -o devops-info-service main.go
```
Run:
```bash
./devops-info-service
```
### 4.3 Environment variables examples
```bash
HOST=127.0.0.1 PORT=3000 ./devops-info-service
DEBUG=true PORT=8081 ./devops-info-service
```
## 5. Challenges & Solutions
I don't know how `go` works.
