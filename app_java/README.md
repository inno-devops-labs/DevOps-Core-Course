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

