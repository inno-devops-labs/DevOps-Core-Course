# DevOps Info Service (Java / Spring Boot)

## Overview

This is the compiled-language version of the DevOps Info Service implemented with Spring Boot. It mirrors the Python API and prepares the project for multi-stage Docker builds.

## Prerequisites

- Java 21+
- Maven 3.9+ (for build and run commands)

## Build and Run

From the `app_java` directory:

```bash
mvn spring-boot:run
```

Or build a runnable JAR:

```bash
mvn clean package
java -jar target/devops-info-service-1.0.0.jar
```

## Configuration

Environment variables are mapped in `src/main/resources/application.properties`:

| Variable | Default | Description |
| --- | --- | --- |
| `HOST` | `0.0.0.0` | Host interface to bind (`server.address`) |
| `PORT` | `8080` | Port to listen on (`server.port`) |

Examples:

```bash
PORT=9090 mvn spring-boot:run
HOST=127.0.0.1 PORT=3000 mvn spring-boot:run
```

## API Endpoints

- `GET /` - Service and system information
- `GET /health` - Health check

## Notes on Schema Parity

The lab requires the same JSON structure as the Python version. To keep schema parity, the `python_version` field is still present but contains the Java runtime version (for example, `java-21`).

