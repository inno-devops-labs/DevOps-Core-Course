[![Go CI](https://github.com/newspec/DevOps-Core-Course/actions/workflows/go-ci.yml/badge.svg?branch=lab03)](https://github.com/newspec/DevOps-Core-Course/actions/workflows/go-ci.yml?query=branch%3Alab03)
[![Coverage](https://codecov.io/gh/newspec/DevOps-Core-Course/branch/lab03/graph/badge.svg)](https://codecov.io/gh/newspec/DevOps-Core-Course?flag=go)
# devops-info-service (Go)

## Overview
`devops-info-service` is a lightweight HTTP service written in Go. It returns:
- service metadata (name, version, description, framework),
- system information (hostname, OS/platform, architecture, CPU count, Go version),
- runtime information (uptime, current UTC time),
- request information (client IP, user-agent, method, path),
- a list of available endpoints.

This is useful for DevOps labs and basic observability: quick environment inspection and health checks.

---

## Prerequisites
- **Go:** 1.22+ (recommended)
- No external dependencies (standard library only)

---

## Installation
```bash
cd app_go
go mod tidy
```

## Running the Application
```bash
go run .
```

## API Endpoints
- `GET /` - Service and system information
- `GET /health` - Health check

## Configuration

The application is configured using environment variables.

| Variable | Default | Description | Example |
|---------|---------|-------------|---------|
| `HOST`  | `0.0.0.0` | Host interface to bind the server to | `0.0.0.0` |
| `PORT`  | `8080` | Port the server listens on | `8080` |
