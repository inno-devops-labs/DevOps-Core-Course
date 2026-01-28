# devops-info-service (Go)

## Overview

This is the Go implementation of the DevOps Info Service. It provides the same API as the Python version.

## Prerequisites

- Go 1.20+ installed

## Build

```bash
go build -o devops-info-service.exe
```

## Run

```
# Default port 8080
./devops-info-service.exe

# Or specify port via environment variable
PORT=3000 ./devops-info-service.exe
```

## API Endpoints

- `GET /` - Service and system information
- `GET /health` - Health check

## Licence

MIT Licence
`To be made`
