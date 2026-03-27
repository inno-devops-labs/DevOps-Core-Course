# DevOps Info Service (Go)

## Overview
Simple Go web service that exposes system/runtime details, health and readiness checks, Prometheus metrics, and structured JSON logs.

## Prerequisites
- Go 1.25+

## Build
```bash
go build -o devops-info-service.out .
```

## Run
```bash
./devops-info-service.out
# Or with custom config
HOST=127.0.0.1 PORT=8080 ./devops-info-service.out
```

## Endpoints
- `GET /` - service + system + runtime + request info
- `GET /health` - health check
- `GET /ready` - readiness check
- `GET /metrics` - Prometheus metrics exposition

## Configuration

| Variable | Default | Description |
| --- | --- | --- |
| `HOST` | `0.0.0.0` | Bind address for the server |
| `PORT` | `5000` | Port to listen on |
