# DevOps Info Service (Go)

## Overview
A small compiled web service that reports service metadata, system info, runtime uptime, and request details.  
It provides two endpoints: `/` (full info) and `/health` (health check).

## Prerequisites
- Go **1.23+**

## Build
```bash
cd app_go
go build -o devops-info-service .
```

## Running the Application

```bash
./devops-info-service
```

## API Endpoints

* `GET /` - Service and system information
* `GET /health` - Health check

## Configuration

```bash
HOST="0.0.0.0"
PORT="8080"
DEBUG="False"
```

## Docker (multi-stage build)

This project includes a **multi-stage Dockerfile**:

* **Stage 1 (builder):** compiles the Go binary
* **Stage 2 (runtime):** copies only the binary into a minimal image

Build final image:

```bash
cd app_go
docker build -t devops-info-go:lab02 .
```

(Optional) build only the builder stage (for size comparison):

```bash
docker build --target builder -t devops-info-go:builder .
```

Run container:

```bash
docker run --rm -p 8080:8080 devops-info-go:lab02
```