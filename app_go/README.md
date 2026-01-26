
# DevOps Course Info Service (Go)

## Overview
Go implementation of the `app_python` DevOps Info Service.

## Prerequisites
- Go 1.22+

## Run
From the `app_go/` directory:

- `go run .`
- `HOST=127.0.0.1 PORT=8080 DEBUG=true go run .`

## Build
- `CGO_ENABLED=0 go build -ldflags "-s -w" -o devops-info-service .`
- `./devops-info-service`

## Endpoints
- `GET /` — returns service/system/runtime/request metadata
- `GET /health` — health check

## Docs
- Implementation details: `docs/LAB01.md`
- Language justification: `docs/GO.md`
