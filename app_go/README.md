# DevOps Info Service — Go Version

![CI/CD](https://github.com/sayfetik/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)

[![Coverage](https://codecov.io/gh/<your-username>/<repo>/branch/main/graph/badge.svg)](https://codecov.io/gh/<your-username>/<repo>)

## Overview

This is a compiled Go implementation of the DevOps Info Service. It provides the same functionality as the Python version but is delivered as a single statically compiled binary.

## Requirements

- Go 1.22 or higher

## Build and Run

Initialize the module (once):

```bash
go mod init devops-info-service
```

## Run

```bash
./devops-info-service
```

Or with custom configuration:

```bash
PORT=9090 ./devops-info-service
```

## API Endpoints

GET / — service and system information

GET /health — health check endpoint
