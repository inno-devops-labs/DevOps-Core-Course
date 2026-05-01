# DevOps Info Service (Go)

Go implementation of the Lab 1 DevOps info service. Exposes two endpoints that return service, system, runtime, and health data with configurable host and port.

## Prerequisites
- Go 1.21+

## Installation
```bash
git clone <this-repo>
cd app_go
# (optional) tidy modules
go mod tidy
```

## Running
```bash
# default: 0.0.0.0:8080
go run main.go

# custom host/port
HOST=127.0.0.1 PORT=3000 go run main.go
```

## API Endpoints
- `GET /` — Service/system/runtime info plus request metadata
- `GET /health` — Health status and uptime

## Configuration
| Env Var | Default | Description |
|---------|---------|-------------|
| `HOST`  | `0.0.0.0` | Interface to bind |
| `PORT`  | `8080` | Port to listen on |

## Example Requests
```bash
curl -s http://localhost:8080/ | jq .
curl -s http://localhost:8080/health | jq .
```

