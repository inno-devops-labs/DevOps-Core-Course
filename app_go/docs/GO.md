# Go Language Justification

## Why Go?

I chose **Go** as the compiled language for the bonus task for the following reasons:

### 1. Simplicity and Readability

Go has a simple, clean syntax that is easy to learn and read. Unlike Rust or Java, Go doesn't require complex constructs to accomplish basic tasks.

```go
// Simple HTTP server in Go
http.HandleFunc("/", mainHandler)
http.ListenAndServe(":8080", nil)
```

### 2. Excellent Standard Library

Go's standard library includes everything needed for web development:
- `net/http` - HTTP server and client
- `encoding/json` - JSON encoding/decoding
- `os` - Environment variables and system info
- `runtime` - Runtime information (GOOS, GOARCH, NumCPU)

No external dependencies required!

### 3. Perfect for Containerization

Go produces statically-linked binaries that:
- Have **no runtime dependencies**
- Can run in minimal containers (scratch, distroless)
- Result in **tiny Docker images** (~5 MB vs ~100+ MB for Python)

This aligns perfectly with the upcoming Lab 2 on containerization.

### 4. Fast Compilation

Go compiles extremely fast, making the development cycle quick:
- Full build: ~1-2 seconds
- Cross-compilation built-in

### 5. Built for Cloud Native

Go was designed at Google for building scalable, cloud-native applications. Many DevOps tools are written in Go:
- Docker
- Kubernetes
- Terraform
- Prometheus
- Grafana

Learning Go provides insight into these tools' internals.

### 6. Cross-Platform Support

Build for any platform from any platform:

```bash
# Build for Linux from Windows
GOOS=linux GOARCH=amd64 go build -o app-linux

# Build for macOS
GOOS=darwin GOARCH=amd64 go build -o app-macos

# Build for Windows
GOOS=windows GOARCH=amd64 go build -o app.exe
```

## Comparison with Alternatives

| Feature | Go | Rust | Java | C# |
|---------|----|----- |------|-----|
| Learning Curve | Easy | Steep | Moderate | Moderate |
| Compilation Speed | Fast | Slow | Moderate | Moderate |
| Binary Size | Small | Small | Large | Large |
| Memory Usage | Low | Very Low | High | Moderate |
| Cloud Native Ecosystem | Excellent | Growing | Mature | Good |
| DevOps Tool Adoption | Very High | Low | Moderate | Low |

### Why Not Rust?

- Steeper learning curve (ownership, borrowing)
- Slower compilation times
- More complex for simple web services

### Why Not Java/C#?

- Larger runtime requirements (JVM, .NET)
- Bigger container images
- More boilerplate code

## Conclusion

Go provides the best balance of:
- **Simplicity** for learning
- **Performance** for production
- **Portability** for containerization
- **Ecosystem alignment** with DevOps tools

This makes it the ideal choice for this course's compiled language implementation.
