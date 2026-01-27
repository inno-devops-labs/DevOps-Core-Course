# DevOps Info Service (Go)

## Overview
Compiled-language version of the DevOps info service. It exposes the same two endpoints as the Python app and keeps the JSON response structure consistent.

## Prerequisites
- Go 1.22+ installed

## Build and Run
Run directly:
```bash
go run main.go
```

Build a binary:
```bash
go build -o devops-info
./devops-info
```

Windows build/run:
```bash
go build -o devops-info.exe
.\devops-info.exe
```

Custom config examples:
```bash
PORT=8080 go run main.go
HOST=127.0.0.1 PORT=3000 go run main.go
```

## API Endpoints
- `GET /` - Service and system information
- `GET /health` - Health check

## Configuration
| Variable | Default | Description |
| --- | --- | --- |
| `HOST` | `0.0.0.0` | Bind address for the server |
| `PORT` | `5000` | Port to listen on |
