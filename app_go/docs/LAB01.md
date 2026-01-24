# Lab 01 - DevOps Info Service: Go Implementation

## Overview

This document details the Go implementation of the DevOps Info Service. The implementation matches the Python FastAPI version's JSON structure while showcasing Go's performance and resource efficiency.

## Implementation Details

### Project Structure
```
app_go/
├── main.go             # Single-file application
├── go.mod              # Module definition
├── README.md           # User documentation
└── docs/
    ├── GO.md           # Language justification
    ├── LAB01.md        # Implementation details
    └── screenshots/    # Deployment proof
```

### Core Components

#### 1. Data Structures
All types are defined with JSON struct tags for automatic marshaling:

```go
// Service metadata
type Service struct {
    Name        string `json:"name"`
    Version     string `json:"version"`
    Description string `json:"description"`
    Framework   string `json:"framework"`
}

// Complete response structure
type FullResponse struct {
    Service   Service              `json:"service"`
    System    SystemInfo           `json:"system"`
    Runtime   RuntimeInfo          `json:"runtime"`
    Request   RequestInfo          `json:"request"`
    Endpoints []map[string]string  `json:"endpoints"`
}
```

**Why Structs Over Maps**: Type safety, compile-time field checking, automatic JSON encoding/decoding.

#### 2. System Information Collection
```go
func mainHandler(w http.ResponseWriter, r *http.Request) {
    hostname, _ := os.Hostname()
    secs, human := uptime()
    
    resp := FullResponse{
        System: SystemInfo{
            Hostname:      hostname,
            Platform:      runtime.GOOS,
            Architecture:  runtime.GOARCH,
            CPUCount:      runtime.NumCPU(),
            GoVersion:      runtime.Version(),
        },
        // ... other fields
    }
}
```

**Differences from Python**:
- `runtime.GOOS` = `platform.system()` (OS name)
- `runtime.GOARCH` = `platform.machine()` (architecture)
- `runtime.NumCPU()` = `os.cpu_count()` (CPU count)
- Platform version maps to architecture (architecture distinguishes Go binaries)

#### 3. Uptime Calculation
```go
// Global start time recorded at startup
var startTime = time.Now().UTC()

// Uptime helper with plural logic
func uptime() (int64, string) {
    secs := int64(time.Since(startTime).Seconds())
    h := secs / 3600
    m := (secs % 3600) / 60
    human := fmt.Sprintf("%d hour%s, %d minute%s", 
        h, pluralize(h), 
        m, pluralize(m))
    return secs, human
}

func pluralize(n int64) string {
    if n != 1 {
        return "s"
    }
    return ""
}
```

**Key Difference**: Go's `time.Since()` is more precise than Python's `datetime` delta for subsecond timing.

#### 4. HTTP Handlers
```go
func mainHandler(w http.ResponseWriter, r *http.Request) {
    // ... build response
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(resp)  // Efficient streaming encoder
}

func main() {
    http.HandleFunc("/", mainHandler)
    http.HandleFunc("/health", healthHandler)
    
    port := os.Getenv("PORT")
    if port == "" {
        port = "8080"  // Default Go port
    }
    http.ListenAndServe(":"+port, nil)
}
```

- `http.HandleFunc` registers route handlers
- Go's `http.Server` automatically spawns goroutines for each request
- Handles thousands of concurrent connections efficiently

## Building and Deployment

### Development Build
```bash
go build -o devops-info-service main.go
./devops-info-service
# Listening on :8080
```

### Production Build (Optimized)
```bash
# Strip debug symbols for smaller binary
go build -ldflags="-s -w" -o devops-info-service main.go
ls -lh devops-info-service
# -rw-r--r-- 1 user 6.2M devops-info-service
```

### Cross-Compilation
```bash
# Linux x86_64
GOOS=linux GOARCH=amd64 go build -o devops-info-service-linux main.go

# Linux ARM (Raspberry Pi, Apple Silicon container)
GOOS=linux GOARCH=arm64 go build -o devops-info-service-arm main.go

# Windows
GOOS=windows GOARCH=amd64 go build -o devops-info-service.exe main.go

# macOS Intel
GOOS=darwin GOARCH=amd64 go build -o devops-info-service-macos main.go
```

**Advantage**: Single `go build` command compiles for any platform without changing code.
