# Lab 01 - DevOps Info Service (Java / Spring Boot)

## Implementation Notes

The compiled-language version is implemented with Spring Boot and mirrors the Python API:
- `GET /`
- `GET /health`

Key implementation files:
- `app_java/src/main/java/com/devopsinfo/DevopsInfoServiceApplication.java`
- `app_java/src/main/java/com/devopsinfo/api/InfoController.java`
- `app_java/src/main/java/com/devopsinfo/service/InfoService.java`
- `app_java/src/main/java/com/devopsinfo/api/RestExceptionHandler.java`

## Configuration

Environment variables are wired through `application.properties`:

```properties
server.address=${HOST:0.0.0.0}
server.port=${PORT:8080}
```

This preserves the lab requirement to configure the app via `HOST` and `PORT`.

## Build and Run

From the `app_java` directory:

```bash
mvn spring-boot:run
curl http://127.0.0.1:8080/
curl http://127.0.0.1:8080/health
```

Or build a runnable JAR:

```bash
mvn clean package
java -jar target/devops-info-service-1.0.0.jar
```

## Schema Parity with Python

The lab asks for the same JSON structure as the Python service. To keep parity, the `python_version` field is still present but contains the Java runtime version (for example, `java-21`).

## Screenshots

Screenshots directory:
- `app_java/docs/screenshots/01-main-endpoint.png`
- `app_java/docs/screenshots/02-health-check.png`
- `app_java/docs/screenshots/03-formatted-output.png`

Replace the placeholder images with real screenshots from your environment.

