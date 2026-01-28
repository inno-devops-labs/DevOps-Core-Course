# DevOps Info Service (Go)

## Overview
A small compiled web service that reports service metadata, system info, runtime uptime, and request details.  
It provides two endpoints: `/` (full info) and `/health` (health check).

## Prerequisites
- Go **1.23+**

## Build
```bash
cd app_go
go build -o devops-info-service .
```

## Running the Application

```bash
./devops-info-service
```

## API Endpoints

* `GET /` - Service and system information
* `GET /health` - Health check

## Configuration

```bash
HOST="0.0.0.0"
PORT="8080"
DEBUG="False"
```