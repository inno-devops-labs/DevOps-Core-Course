# DevOps Info Service (Go)

A lightweight web service providing system and runtime information, built with Go's standard library.

## Prerequisites

- Go 1.21 or higher

## Installation

No external dependencies required - uses only Go standard library.

```bash
go mod download
```

## Building

```bash
# Build for current platform
go build -o devops-service main.go

# Build for Linux (cross-compile from any OS)
GOOS=linux GOARCH=amd64 go build -o devops-service-linux main.go

# Build for Windows
GOOS=windows GOARCH=amd64 go build -o devops-service.exe main.go
```

## Running

```bash
# Run directly without building
go run main.go

# Or use the compiled binary
./devops-service

# Custom port configuration
PORT=3000 ./devops-service
```

## API Endpoints

### GET /
Returns comprehensive service and system information including:
- Service metadata (name, version, framework)
- System details (hostname, platform, architecture, CPU count, Go version)
- Runtime metrics (uptime, current time)
- Request information (client IP, user agent, method, path)

### GET /health
Health check endpoint returning service status and uptime.
Used for monitoring and Kubernetes liveness/readiness probes.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8080` | Server listening port |

## Binary Size Comparison

```bash
# Go binary (statically linked, no dependencies)
$ ls -lh devops-service
-rwxr-xr-x  7.2M  devops-service

# Python container (requires interpreter + dependencies)
$ docker images python:3.11-slim
python:3.11-slim  ~120 MB
```

Go produces a self-contained executable that is **~17x smaller** than a Python container image.

## Testing

### Running Tests Locally

```bash
# Run all tests
go test -v .

# Run tests with coverage
go test -v -coverprofile=coverage.out .
go tool cover -func=coverage.out

# View coverage in HTML
go tool cover -html=coverage.out
```

### Test Structure

Tests are organized into separate files following best practices:

```
app_go/
├── root_test.go      # Tests for GET / endpoint (7 tests)
├── health_test.go    # Tests for GET /health endpoint (2 tests)
├── errors_test.go    # Tests for error handling (404 responses) (1 test)
└── runtime_test.go   # Tests for runtime calculations (4 tests)
```

**Benefits of this structure:**
- **Separation of concerns:** Each file focuses on a specific endpoint or aspect
- **Better maintainability:** Easy to find and update tests for specific functionality
- **Improved readability:** Smaller, focused files are easier to understand
- **Scalability:** Easy to add new test files as the application grows

### Test Coverage

The test suite includes:
- ✅ Main endpoint (`GET /`) - JSON structure, service info, system info validation
- ✅ Health endpoint (`GET /health`) - Status, timestamp, uptime validation
- ✅ Error handling (404 responses)
- ✅ Runtime calculations (uptime formatting)
- ✅ Helper functions (`formatUptime`)
- ✅ Request info capture (method, user agent)
- ✅ System info details (platform, architecture)
- ✅ Uptime progression (multiple requests)

**Total:** 14 test functions covering all endpoints and core functionality

**Coverage:** 71.4% (exceeds CI threshold of 70%)
- `mainHandler`: 100% coverage (including error handling for `os.Hostname()`)
- **Note:** `main()` function (entry point) is not unit-testable and reduces total coverage
- **All testable functions are 100% covered:** `getRuntime`, `formatUptime`, `mainHandler`, `healthHandler`
- **Coverage breakdown:**
  - `getRuntime`: 100%
  - `formatUptime`: 100%
  - `mainHandler`: 100%
  - `healthHandler`: 100%
  - `main`: 0% (not unit-testable by design)

### Manual Testing

```bash
# Start the service
./devops-service

# In another terminal
curl http://localhost:8080/ | jq
curl http://localhost:8080/health
```