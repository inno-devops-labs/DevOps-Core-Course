# DevOps Info Service

## Overview
A simple Python web service that returns service info, system information, runtime uptime, and request details.

## Prerequisites
- Java 21
- Gradle (or Gradle Wrapper `./gradlew`)

## Installation
```bash
./gradlew clean build
```

## Running the Application
Run via Gradle
```bash
./gradlew bootRun
```
Run as a jar
```bash
./gradlew build
java -jar build/libs/*.jar
```
Custom config:
```bash
PORT=8080 ./gradlew bootRun
# or
HOST=127.0.0.1 PORT=3000 ./gradlew bootRun
```

## API Endpoints
- GET `/` — Service and system information
- GET `/health` — Health check

## Configuration
| Variable            | Default                    | Description         |
| ------------------- | -------------------------- | ------------------- |
| HOST                | 0.0.0.0                    | Bind address        |
| PORT                | 5000                       | Listen port         |
| SERVICE_NAME        | devops-info-service        | Service name        |
| SERVICE_VERSION     | 1.0.0                      | Service version     |
| SERVICE_DESCRIPTION | DevOps course info service | Service description |

## Docker
### Build image (local)
From the `app_java/` directory, build an image using the current folder as the build context:
```bash
docker build -t <image-name>:<tag> .
```

### Run container
Run the container with port publishing so the service is reachable from the host:
```bash
docker run --rm -p <host-port>:<container-port> gghost1/devops-lab-app-java:latest
```
Pass configuration via environment variables (the app reads HOST, PORT, DEBUG):
```bash
docker run --rm -e PORT=<port> -p <port>:<port> gghost1/devops-lab-app-java:latest
```
For local built image replace `gghost1/devops-lab-app-java:latest` on your `<image-name>:<tag>`.

### Pull from Docker Hub
Pull an already published image from Docker Hub:
```bash
docker pull gghost1/devops-lab-app-java:latest
```