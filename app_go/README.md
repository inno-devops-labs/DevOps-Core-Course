# DevOps Info Service (Go)

[![Go CI](https://github.com/abdughafforzoda/DevOps-Core-Course/actions/workflows/go-ci.yml/badge.svg)](https://github.com/abdughafforzoda/DevOps-Core-Course/actions/workflows/go-ci.yml)

Go implementation of the DevOps Info Service — same endpoints and JSON structure as the Python version. Used for Lab 1 bonus and as a basis for multi-stage Docker builds in Lab 2.

## Prerequisites

- **Go 1.21+** (1.24 used during development)

## Build

```bash
cd app_go

# Standard build
go build -o devops-info-service .

# Smaller binary (strip debug info) — recommended for Docker
go build -ldflags="-s -w" -o devops-info-service .
```

## Run

```bash
./devops-info-service
```

Defaults: `HOST=0.0.0.0`, `PORT=5000`.

Custom config:

```bash
PORT=8080 ./devops-info-service
HOST=127.0.0.1 PORT=3000 ./devops-info-service
```

## API Endpoints

- **`GET /`** — Service, system, runtime, and request info + endpoints list.
- **`GET /health`** — Health check (`status`, `timestamp`, `uptime_seconds`).

## Configuration

| Variable | Default   | Description        |
|----------|-----------|--------------------|
| `HOST`   | `0.0.0.0` | Bind address       |
| `PORT`   | `5000`    | Listen port        |

## Binary size vs Python

| Build | Size   |
|-------|--------|
| `go build` (default) | ~8.1 MB |
| `go build -ldflags="-s -w"` | ~5.5 MB |

Python runs via interpreter + virtualenv; there is no single executable. The Go binary is self-contained and suitable for minimal Docker images (e.g. `scratch` or `alpine`).

## Test

```bash
cd app_go
go test -v ./...
```

## Docker

Multi-stage build (Lab 2 bonus):

```bash
docker build -t devops-info-service-go .
docker run -p 5000:5000 devops-info-service-go
```

See `docs/LAB02.md` for the multi-stage strategy and size analysis.

## Test

```bash
curl -s http://localhost:5000/ | jq
curl -s http://localhost:5000/health | jq
```
