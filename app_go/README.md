# Lab01 — DevOps Info Service

## Overview

**DevOps Info Service (Go version)** is a lightweight web application written in Go that provides detailed information about the service itself, the system it runs on, and its runtime environment.

This implementation is part of the **bonus task** for Lab 01 and is intended to demonstrate the advantages of using a compiled language in DevOps workflows, especially for containerization and multi-stage Docker builds.

**Features:**

* `GET /` — returns service, system, runtime, and request information
* `GET /health` — simple health check endpoint
* Configurable via environment variables

---

## Prerequisites

* Go **1.24.5**

---

## Installation

1. Clone the repository:

```bash
git clone https://github.com/<your-username>/DevOps-Core-Course.git
```

2. Navigate to the Go application directory:

```bash
cd app_go
```

3. Initialize Go module (if not already initialized):

```bash
go mod init devops-info-service
```

---

## Running the Application

### Run directly

```bash
cd app_go
go run main.go
```

By default, the service runs on:

```
http://0.0.0.0:5000
```

### Run with custom configuration

```bash
HOST=127.0.0.1 PORT=8080 go run main.go
```

---

## API Endpoints

### `GET /`

Returns detailed information about the service and the system.

**Example:**

```json
{
  "endpoints": [
    {
      "description": "Service information",
      "method": "GET",
      "path": "/"
    },
    {
      "description": "Health check",
      "method": "GET",
      "path": "/health"
    }
  ],
  "request": {
    "client_ip": "::1",
    "method": "GET",
    "path": "/",
    "user_agent": "Mozilla/5.0 (Windows NT; Windows NT 10.0; ru-RU) WindowsPowerShell/5.1.26100.7462"
  },
  "runtime": {
    "current_time": "2026-01-28T08:32:20Z",
    "timezone": "UTC",
    "uptime_human": "0 hours, 24 minutes",
    "uptime_seconds": 1452
  },
  "service": {
    "description": "DevOps course info service",
    "framework": "net/http",
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "system": {
    "architecture": "amd64",
    "cpu_count": 16,
    "go_version": "go1.24.5",
    "hostname": "Daniil",
    "platform": "windows",
    "platform_version": "go1.24.5"
  }
}
```

---

### `GET /health`

Returns service health status.

**Example:**

```bash
curl http://localhost:8080/health
```

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T08:33:26Z",
  "uptime_seconds": 1518
}
```

---

## Configuration

The application can be configured using environment variables:

| Environment Variable | Default   | Description                        |
| -------------------- | --------- | ---------------------------------- |
| `HOST`               | `0.0.0.0` | Host address to bind the server    |
| `PORT`               | `8080`    | Port to run the application on     |

---

## Project Structure

```
app_go/
├── main.go
├── go.mod
├── README.md
└── docs/
    ├── LAB01.md
    └── screenshots/
```
