# DevOps Info Service (Java/Spring Boot)

A comprehensive web service built with Java 21 and Spring Boot 3 that provides detailed information about itself and its runtime environment. This is the bonus implementation for Lab 1.

## Overview

This service provides the same functionality as the Python version but implemented using enterprise-grade Java technologies. It demonstrates the differences between interpreted and compiled languages for DevOps applications.

## Prerequisites

- **Java:** JDK 21 or higher
- **Maven:** 3.9+ for building
- **Memory:** At least 512 MB RAM

## Building the Application

```powershell
# Navigate to app directory
cd app_java

# Set Maven in PATH (if not permanent)
$env:PATH = "C:\Users\пк\maven\apache-maven-3.9.6\bin;$env:PATH"

# Build the application
mvn clean package

# This creates: target/devops-info-service.jar (~20 MB)
```

## Running the Application

### Default Configuration

```powershell
java -jar target/devops-info-service.jar
```

Application will start on http://localhost:8080

### Custom Port

```powershell
java -jar target/devops-info-service.jar --server.port=9090
```

### Environment Variables

```powershell
$env:SERVER_PORT=8080; java -jar target/devops-info-service.jar
```

## API Endpoints

### `GET /`

Returns comprehensive service and system information (same structure as Python version).

**Example Request:**
```powershell
curl http://localhost:8080/ -UseBasicParsing
```

### `GET /health`

Health check endpoint for monitoring.

**Example Request:**
```powershell
curl http://localhost:8080/health -UseBasicParsing
```

## Configuration

Application can be configured via `application.properties` or environment variables:

| Property | Default | Description |
|----------|---------|-------------|
| `server.port` | `8080` | Server port |
| `app.version` | `1.0.0` | Application version |
| `logging.level.root` | `INFO` | Log level |

## Project Structure

```
app_java/
├── pom.xml                           # Maven configuration
├── .gitignore                        # Git ignore rules
├── README.md                         # This file
├── src/
│   └── main/
│       ├── java/com/devops/info/
│       │   ├── Application.java      # Main class
│       │   ├── controller/
│       │   │   └── InfoController.java  # REST controller
│       │   └── model/                # Data models
│       │       ├── ServiceResponse.java
│       │       ├── ServiceInfo.java
│       │       ├── SystemInfo.java
│       │       ├── RuntimeInfo.java
│       │       ├── RequestInfo.java
│       │       ├── EndpointInfo.java
│       │       └── HealthResponse.java
│       └── resources/
│           └── application.properties  # Configuration
└── docs/                             # Documentation
    ├── JAVA.md                       # Language justification
    ├── LAB01.md                      # Lab submission
    └── screenshots/                  # Evidence
```

## Comparison with Python Version

| Aspect | Python/Flask | Java/Spring Boot |
|--------|--------------|------------------|
| **Lines of Code** | ~170 | ~350 |
| **Startup Time** | <1 second | 3-5 seconds |
| **Memory Usage** | ~30 MB | ~150 MB |
| **Binary Size** | N/A (interpreted) | ~20 MB JAR |
| **Build Time** | N/A | 30-60 seconds |
| **Performance** | Good | Excellent (after warmup) |
| **Type Safety** | Runtime | Compile-time |

## Testing

```powershell
# Start the application
java -jar target/devops-info-service.jar

# In another terminal, test endpoints
(curl http://localhost:8080/ -UseBasicParsing).Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
(curl http://localhost:8080/health -UseBasicParsing).Content | ConvertFrom-Json | ConvertTo-Json
```

## Troubleshooting

### OutOfMemoryError

Increase heap size:
```powershell
java -Xmx512m -jar target/devops-info-service.jar
```

### Port Already in Use

Change the port:
```powershell
java -jar target/devops-info-service.jar --server.port=9090
```

### Build Failures

Ensure Java 21 is being used:
```powershell
java -version
mvn -version
```

## Why Java/Spring Boot?

- **Enterprise Standard:** Spring Boot is the most popular Java framework for microservices
- **Production Ready:** Built-in health checks, metrics, and monitoring
- **Type Safety:** Compile-time error checking prevents many runtime bugs
- **Performance:** After JVM warmup, performance exceeds Python
- **Ecosystem:** Massive library ecosystem for enterprise needs

## Future Enhancements

This service will be containerized in Lab 2 using multi-stage Docker builds to reduce the final image size from ~500 MB to ~200 MB.

## License

Educational project for DevOps Core Course.

## Author

Created as part of Lab 1 Bonus Task - DevOps Engineering: Core Practices
