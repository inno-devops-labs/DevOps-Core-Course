# DevOps Info Service (Go)

A web service that reports system information and health status, built with Go's standard library `net/http`.

## Prerequisites

- Go 1.21+

## Build

```bash
go build -o devops-info-service
```

## Running the Application

```bash
./devops-info-service
```

With custom configuration:

```bash
PORT=3000 ./devops-info-service
HOST=127.0.0.1 PORT=3000 ./devops-info-service
```

Or run directly without building:

```bash
go run main.go
```

The service starts on `http://localhost:8080` by default.

## API Endpoints

| Method | Path      | Description                          |
|--------|-----------|--------------------------------------|
| GET    | `/`       | Service and system information       |
| GET    | `/health` | Health check (status, uptime)        |

### `GET /`

```bash
curl http://localhost:8080/
```

### `GET /health`

```bash
curl http://localhost:8080/health
```

## Configuration

| Variable | Default   | Description          |
|----------|-----------|----------------------|
| `HOST`   | `0.0.0.0` | Server bind address  |
| `PORT`   | `8080`    | Server port          |

## Binary Size Comparison

| Artifact             | Size     |
|----------------------|----------|
| Python (source)      | ~5 KB    |
| Go (compiled binary) | ~7 MB    |

The Go binary is self-contained — no runtime, no dependencies, no virtual environment needed. Just copy and run.
