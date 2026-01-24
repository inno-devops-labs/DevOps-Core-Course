# Build and run commands:

```bash
cd app_java

# Compile
javac Main.java

# Run with defaults (0.0.0.0:8080)
java Main

# Run with custom port
PORT=5000 java Main

# Run with custom host and port
HOST=127.0.0.1 PORT=3000 java Main
```

# Test in another terminal:

```bash
curl http://localhost:8080/
curl http://localhost:8080/health
```

This is pure Java 21 with:

- No external dependencies (uses built-in `com.sun.net.httpserver`)
- Text blocks (Java 15+) for clean JSON formatting
- Single file implementation
- Both endpoints with identical JSON structure
- Environment variable configuration
- Logging to stdout