# Lab 1 Bonus - DevOps Info Service (Java)

## Implementation Approach

### Pure Java 21 with Built-in HTTP Server

Implemented using **Java 21** with `com.sun.net.httpserver.HttpServer` - no external dependencies required.

**Key advantages:**

- Zero external dependencies - single source file
- Built-in HTTP server included in JDK
- Type safety at compile time
- Familiar patterns for Java developers
- Small JAR size for containerization

### Why No Framework?

For this simple service, a full framework (Spring Boot, Quarkus) would be overkill:

- HttpServer provides sufficient functionality
- Reduces complexity and startup time
- Smaller binary size for Docker (Lab 2)
- Demonstrates core Java capabilities

## Best Practices Applied

### 1. Environment-Based Configuration

**Importance:** 12-factor app principle - configuration separate from code.

**Implementation:**

```java
String host = System.getenv().getOrDefault("HOST", "0.0.0.0");
int port = Integer.parseInt(System.getenv().getOrDefault("PORT", "8080"));
```

### 2. Structured Response Building

**Importance:** Maintainable JSON generation without external libraries.

**Implementation:**

```java
private static String buildMainResponse(String clientIp, String userAgent, 
                                       String method, String path) {
    return String.format("""
        {
          "service": { ... },
          "system": { ... }
        }
        """, ...);
}
```

### 3. Text Blocks (Java 15+)

**Importance:** Clean, readable JSON formatting without escape characters.

**Implementation:**

```java
String json = """
    {
      "status": "healthy",
      "timestamp": "%s"
    }
    """.formatted(timestamp);
```

### 4. Proper HTTP Response Handling

**Importance:** Correct Content-Type headers and response codes.

**Implementation:**

```java
private static void sendResponse(HttpExchange exchange, int statusCode, String response) 
        throws IOException {
    exchange.getResponseHeaders().set("Content-Type", "application/json");
    byte[] bytes = response.getBytes(StandardCharsets.UTF_8);
    exchange.sendResponseHeaders(statusCode, bytes.length);
    try (OutputStream os = exchange.getResponseBody()) {
        os.write(bytes);
    }
}
```

### 5. Request Logging

**Importance:** Track incoming requests for monitoring.

**Implementation:**

```java
System.out.println(String.format("%s Request: %s %s from %s",
    Instant.now().toString(), method, path, clientIp));
```

### 6. Clean Code Structure

**Importance:** Single-responsibility functions for maintainability.

**Implementation:**
- `handleRoot()` - Main endpoint logic
- `handleHealth()` - Health check logic
- `buildMainResponse()` - JSON construction
- `sendResponse()` - HTTP response helper

## API Documentation

### Main Endpoint: GET /

**Request:**

```bash
curl http://localhost:8080/
```

**Response:**
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Java HttpServer"
  },
  "system": {
    "hostname": "MacNexonm",
    "platform": "Mac OS X",
    "platform_version": "14.5",
    "architecture": "aarch64",
    "cpu_count": 8,
    "java_version": "21.0.7"
  },
  "runtime": {
    "uptime_seconds": 180,
    "uptime_human": "0 hours, 3 minutes",
    "current_time": "2026-01-24T17:32:00.000Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/8.7.1",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/health", "method": "GET", "description": "Health check"}
  ]
}
```

### Health Check: GET /health

**Request:**

```bash
curl http://localhost:8080/health
```

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2026-01-24T17:32:00.000Z",
  "uptime_seconds": 180
}
```

### Build & Run Commands

```bash
# Compile
javac Main.java

# Run with defaults (0.0.0.0:8080)
java Main

# Run with custom port
PORT=5000 java Main

# Run with custom host and port
HOST=127.0.0.1 PORT=3000 java Main
```

## Testing Evidence

### Screenshots

**01-main-endpoint.png**

![Main Endpoint](screenshots/01-main-endpoint.png)

Shows complete JSON response from `GET /` endpoint with all required fields: service metadata (including Java version and framework), system information, runtime details, request information, and endpoints list.

**02-health-check.png**

![Health Check](screenshots/02-health-check.png)

Shows `GET /health` endpoint returning healthy status with timestamp and uptime in seconds.

**03-compilation.png**

![Compilation and Execution](screenshots/03-compilation.png)

Shows Java compilation process and application startup logs including host, port, and Java version information.

### Terminal Output

All endpoints tested successfully:

- Main endpoint returns complete system information
- Health check returns proper status
- Environment variable configuration works (PORT, HOST)
- Application compiles without errors
- Single `.class` file generated (~8KB)
- Request logging works correctly

## Binary Size Comparison

**Java vs Python:**

| Metric | Java | Python |
|--------|------|--------|
| Source Size | ~7KB (Main.java) | ~6KB (app.py) |
| Compiled Size | ~8KB (Main.class) | N/A |
| JAR Size | ~3KB (single class) | N/A |
| Runtime Required | JRE 21+ | Python 3.11+ + dependencies |
| Startup Time | ~100ms | ~50ms |
| Memory Usage | ~30MB (JVM) | ~20MB (interpreter) |

**Docker Benefit:** JAR file can be copied to minimal JRE image, reducing final image size significantly compared to full JDK.

## Challenges & Solutions

### Challenge 1: No External Dependencies

**Problem:** Need to generate JSON manually without libraries like Jackson or Gson.

**Solution:** 

- Used Java 15+ text blocks for clean multi-line strings
- String.format() for value injection
- Keeps application simple and dependency-free

### Challenge 2: Favicon Requests

**Problem:** Browser automatically requests `/favicon.ico`, cluttering logs.

**Solution:**

- Can be filtered or handled with 204 No Content response if needed
- Not critical for API service

## Comparison with Python Version

**Similarities:**

- Both implement identical JSON structure
- Both support environment variable configuration
- Both provide same two endpoints

**Differences:**

- Java requires compilation step
- Java has built-in HTTP server (no pip install)
- Java provides compile-time type safety
- Python has smaller startup overhead
- Python has cleaner dependency management

**Best For:**
- **Java:** Enterprise environments, when JVM is already present, type safety critical
- **Python:** Quick prototypes, scripting, when interpreter is preferred
