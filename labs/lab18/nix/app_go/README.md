![CI](https://github.com/sayfetik/DevOps-Core-Course/actions/workflows/go-ci.yml/badge.svg)

[![Coverage Status](https://coveralls.io/repos/github/sayfetik/DevOps-Core-Course/badge.svg?branch=lab03)](https://coveralls.io/github/sayfetik/DevOps-Core-Course?branch=lab03)

# DevOps Info Service

## Overview
A simple Go web service that provides system and runtime information.

## Requirements
- Go 1.22+

## Run
```bash
go run main.go
```

## API Endpoints
- **GET /** - Service and system information
- **GET /health** - Health check


## Docker

This application can be run inside a Docker container.

### Build Docker Image

Use Docker to build the image locally from the Dockerfile:

```bash
docker build -t info-service .
```

### Run Docker Container

Run the container and expose the application port to the host:

```bash
docker run -p <host_port>:<container_port> info-service
```

You can also configure the service using environment variables:

```bash
docker run -e PORT=<port> -p <host_port>:<port> info-service
```

### Pull Image from Docker Hub

If the image is published to Docker Hub, it can be pulled directly:

```bash
docker pull <dockerhub_username>/info-service
```
