# DevOps Info Service (Go Implementation)

This is a compiled version of the DevOps Info Service, implemented in Go to demonstrate the benefits of static binaries and efficient runtime performance.

## Prerequisites

* Go: 1.21 or higher

## Build and Run

### Run from source

To run the application without manual compilation:
```bash
go run main.go
```

### Build binary

To compile the application into a standalone executable:
```bash
# Windows
go build -o service.exe main.go

# Linux/macOS
go build -o service main.go
```

## Configuration

The application supports the following environment variables:

| Variable | Default   | Description                                                 |
| -------- | --------- | ----------------------------------------------------------- |
| `HOST`   | `0.0.0.0` | IP address to bind the server                               |
| `PORT`   | `5000`    | Port number to run the application                          |

## API Endpoints

* `GET /`: Full system and service metadata.

* `GET /health`: Basic health check status.