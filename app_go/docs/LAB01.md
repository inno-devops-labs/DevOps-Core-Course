# lab 01 submission (go bonus)

## implementation overview

this is the bonus go implementation of the devops info service, providing the same functionality as the python version with identical json response structures

## endpoints implemented

### get /

returns comprehensive service and system information including:
- service metadata (name, version, description, framework)
- system info (hostname, platform, architecture, cpu count, go version)
- runtime info (uptime, current time, timezone)
- request info (client ip, user agent, method, path)
- available endpoints list

### get /health

returns health check information:
- status: healthy
- timestamp in iso format
- uptime in seconds

## code structure

```go
// struct definitions for json responses
type ServiceInfo struct { ... }
type SystemInfo struct { ... }
type RuntimeInfo struct { ... }
type RequestInfo struct { ... }
type MainResponse struct { ... }
type HealthResponse struct { ... }
type ErrorResponse struct { ... }

// helper function for uptime calculation
func getUptime() (int, string) { ... }

// http handlers
func mainHandler(w http.ResponseWriter, r *http.Request) { ... }
func healthHandler(w http.ResponseWriter, r *http.Request) { ... }
func notFoundHandler(w http.ResponseWriter, r *http.Request) { ... }

// application entry point
func main() { ... }
```

## features

### environment variable configuration

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

### error handling

custom 404 handler returns json error response:

```go
func notFoundHandler(w http.ResponseWriter, r *http.Request) {
    response := ErrorResponse{
        Error:   "Not Found",
        Message: "The requested endpoint does not exist",
        Path:    r.URL.Path,
    }
    w.WriteHeader(http.StatusNotFound)
    json.NewEncoder(w).Encode(response)
}
```

### logging

request logging using standard log package:

```go
log.Printf("Request received: %s %s", r.Method, r.URL.Path)
```

## testing evidence

![[fullscreen with two terminals: left running go app on port 8080, right showing curl responses for main and health endpoints]](screenshots/go-implementation.png)

## build and run

```bash
# build
go build -o devops-info-service main.go

# run
./devops-info-service

# or directly
go run main.go
```

## differences from python version

| aspect | python | go |
|--------|--------|-----|
| framework field | Flask | net/http |
| python_version | included | replaced with go_version |
| default port | 5000 | 8080 |
| timestamp format | isoformat with microseconds | rfc3339 |
| client_ip | ip only | ip:port |
