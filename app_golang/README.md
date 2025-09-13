# Golang Web Application

## Features

- Displays the current time in Moscow.

## Requirements

- Go 1.18 or later
- golangci-lint

## Installation

Install dependencies (Go modules):

```bash
go mod tidy
```

## Usage

1. Run the application:

   ```bash
   go run main.go
   ```

2. Open your browser and navigate to:

   ```curl
   http://127.0.0.1:8080
   ```

## Testing

Run tests:

```bash
go test ./...
```

## Formatting

```bash
go fmt ./...
```

## Linting

```bash
golangci-lint run
```
