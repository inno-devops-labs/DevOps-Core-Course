# DevOps Info Service

A web application providing detailed system information and health status for DevOps monitoring.

## Overview

This service provides comprehensive information about:
- Service metadata (name, version, description)
- System information (hostname, platform, CPU, etc.)
- Runtime information (uptime, current time)
- Request details (client IP, user agent)
- Health status for monitoring

## Prerequisites

- Java 21 or higher
- Maven

## Installation

1. Clone the repository

## Building
```bash
mvn clean package
```

## Running the Application
```bash
java -jar target/app_java-0.0.1-SNAPSHOT.jar
```

With custom configuration:
```bash
PORT=8080 java -jar target/app_java-0.0.1-SNAPSHOT.jar
HOST=127.0.0.1 PORT=3000 java -jar target/app_java-0.0.1-SNAPSHOT.jar
DEBUG=true java -jar target/app_java-0.0.1-SNAPSHOT.jar
```

## API Endpoints
- GET / - Service and system information
- GET /health - Health check


## Configuration
| Variable | Default   | Description                     |
| -------- | --------- | ------------------------------- |
| `HOST`   | `0.0.0.0` | Host to bind the server to      |
| `PORT`   | `5000`    | Port to listen on               |
| `DEBUG`  | `False`   | Enable debug mode               |
