# DevOps Info Service (Go)

Go implementation of the DevOps Info Service for **DevOps Core Course — Lab 1 (Bonus)**.

## Overview
This service provides:
- `GET /` — JSON with service metadata, system info, runtime info, request info, and available endpoints
- `GET /health` — JSON health check with uptime
- JSON structure matches the Python version (per course requirement)

## Prerequisites
- Go 1.20+

## Run (Development)
```bash
cd app_go
go run .
```

## Build
```bash
cd app_go
go build -o devops-info-service .
./devops-info-service
```

## Configuration
| Variable | Default | Description |
|---|---:|---|
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `8080` | Listening port |

Example:
```bash
HOST=127.0.0.1 PORT=8080 go run .
```

## API Endpoints

### `GET /`
Example:
```bash
curl -s http://localhost:8080/ | head
```

### `GET /health`
Example:
```bash
curl -s http://localhost:8080/health
```

### 404 behavior
Example:
```bash
curl -i http://localhost:8080/does-not-exist
```

## Screenshots
See: `app_go/docs/screenshots/`

- Main page: `docs/screenshots/main_page.png`  
  ![](docs/screenshots/main_page.png)

- Healthcheck: `docs/screenshots/healthcheck.png`  
  ![](docs/screenshots/healthcheck.png)

- Terminal curl tests: `docs/screenshots/terminal_curl.png`  
  ![](docs/screenshots/terminal_curl.png)

## Notes
- For strict bonus acceptance, it may be useful to add a screenshot showing the compilation step (`go build`).
