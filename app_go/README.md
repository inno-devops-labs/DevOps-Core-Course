# DevOps Info Service - Go Implementation

A simple HTTP service in Go that provides system information and health check endpoints. This is the compiled language implementation paired with the Python version in the monorepo.

## Features

- **GET /** - Returns system and service information
- **GET /health** - Returns health check status
- **GET /info** - Alias for root endpoint
- Built with Go 1.21 (statically compiled, minimal Docker image)
- JSON API responses
- Environment-based configuration

## Prerequisites

- Go 1.21 or higher
- (Optional) Docker for containerized deployment

## Installation & Running

### Local Development

```bash
cd app_go

# Run the application (default port 8080)
go run main.go

# Or specify a custom port
PORT=9000 go run main.go
```

### Testing

```bash
cd app_go

# Run all tests
go test -v ./...

# Run tests with coverage
go test -v -cover ./...

# Generate coverage report
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

### Building

```bash
cd app_go

# Build binary
go build -o devops-info-service-go

# Run the binary
./devops-info-service-go
```

## Docker

### Build locally

```bash
docker build -t devops-info-service-go:local app_go
docker run -p 8080:8080 devops-info-service-go:local
```

### Pull from Docker Hub

```bash
docker pull username/devops-info-service-go:latest
docker run -p 8080:8080 username/devops-info-service-go:latest
```

### Available Tags

Each successful CI build generates:
- `username/devops-info-service-go:2024.02.11` (date version)
- `username/devops-info-service-go:2024.02.11-a1b2c3d` (date + commit)
- `username/devops-info-service-go:latest` (latest build)

## API Endpoints

### GET /health

Health check endpoint.

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2024-02-11T10:30:45Z",
  "uptime_seconds": 127
}
```

### GET / or /info

System and service information.

**Response (200):**
```json
{
  "service": {
    "name": "devops-info-service-go",
    "version": "1.0.0",
    "description": "DevOps course info service in Go",
    "language": "Go"
  },
  "system": {
    "os": "linux",
    "architecture": "amd64",
    "go_version": "go1.21.0"
  },
  "runtime": {
    "uptime_seconds": 127,
    "timestamp": "2024-02-11T10:30:45Z"
  }
}
```

## Configuration

Environment Variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8080` | Server port |

## CI/CD Pipeline

This application has its own GitHub Actions workflow with **path-based triggers**.

### Python vs. Go CI

**Path-based Triggers:**
- **Python workflow** runs only when `app_python/` files change
- **Go workflow** runs only when `app_go/` files change
- Changes to documentation or other apps don't trigger unnecessary builds
- Both workflows can run in parallel

**Workflow File:** [`.github/workflows/go-ci.yml`](../../.github/workflows/go-ci.yml)

**Pipeline Stages:**
1. **Test & Lint** - Go testing, golangci-lint, coverage reports
2. **Build & Push** - Docker build and push to Docker Hub (main/master only)
3. **Notification** - Status summary

**Versioning:** Calendar Versioning (CalVer) - `YYYY.MM.DD` format

### Running CI Locally

```bash
cd app_go

# Install golangci-lint
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest

# Run linting
golangci-lint run

# Run tests
go test -v -cover ./...

# Build Docker image
docker build -t devops-info-service-go:local .
```

## Testing

### Unit Tests

The project includes 5 comprehensive unit tests:

1. **TestHealthEndpoint** - Validates health check response
2. **TestInfoEndpoint** - Validates info endpoint response
3. **TestHealthEndpointHeaders** - Validates Content-Type header
4. **TestInfoEndpointHeaders** - Validates Content-Type header
5. Additional integration tests

**Run tests:**
```bash
go test -v ./...
```

**Test Coverage Goal:** 80%+

## Monitoring CI Builds

GitHub Actions automatically runs the Go CI workflow when:
- Code is pushed to `app_go/` directory
- Workflow file changes
- Dependency files change (go.mod, go.sum)

**Check Status:**
1. Go to GitHub Actions tab
2. Click "Go CI/CD" workflow
3. View latest run
4. Expand steps to see logs

## Benefits of Path-Based Triggers

In a monorepo with multiple applications:

[YES] **No redundant builds** - Python CI doesn't run when only Go code changes  
[YES] **Parallel execution** - Python and Go workflows run independently  
[YES] **Faster feedback** - Developers get results only for changed apps  
[YES] **Resource efficiency** - GitHub Actions minutes only spent on relevant changes  
[YES] **Cleaner logs** - Easier to find relevant workflow runs  

### Example Scenarios

**Scenario 1: Update Python code**
```
[YES] Python workflow runs
[NO] Go workflow skipped (no changes)
```

**Scenario 2: Update Go code**
```
[NO] Python workflow skipped (no changes)
[YES] Go workflow runs
```

**Scenario 3: Update both in single commit**
```
[YES] Python workflow runs
[YES] Go workflow runs (in parallel)
```

**Scenario 4: Update README.md only**
```
[NO] Python workflow skipped
[NO] Go workflow skipped
```

## Multi-Language Strategy

This monorepo contains multiple applications:
- **app_python/** - Python/FastAPI service
- **app_go/** - Go HTTP service

Each has:
- [YES] Separate CI workflow
- [YES] Separate Docker image
- [YES] Separate test suite
- [YES] Path-based triggers
- [YES] CalVer versioning
- [YES] Independent deployment

## Resources

- [Go Standard Library](https://golang.org/pkg/)
- [HTTP Testing](https://golang.org/pkg/net/http/httptest/)
- [golangci-lint](https://golangci-lint.run/)
- [GitHub Actions](https://docs.github.com/en/actions)

## Support

See main [README.md](../../README.md) for project overview and setup instructions.
