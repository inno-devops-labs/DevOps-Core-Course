# DevOps Info Service (Go) — Bonus Task

## Overview
A Go implementation of the DevOps Info Service. It provides two endpoints:
- `GET /` returns service/system/runtime/request information in JSON
- `GET /health` returns a simple health status JSON

## Prerequisites
- Go installed (check with `go version`)

## Run (from source)
```bash
go run .
```
By default the service listens on `0.0.0.0:8080`.

### Custom configuration

```bash
HOST=127.0.0.1 PORT=9090 go run .
```

## Build (binary)

```bash
go build -o devops-info-service
```

## Run (binary)

```bash
./devops-info-service
```

### Custom configuration (binary)

```bash
HOST=127.0.0.1 PORT=9090 ./devops-info-service
```

## API Endpoints

### GET /

```bash
curl -s http://127.0.0.1:8080/ | python -m json.tool
```

### GET /health

```bash
curl -s http://127.0.0.1:8080/health | python -m json.tool
```
