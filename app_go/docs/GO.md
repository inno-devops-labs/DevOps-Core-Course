# Why Go?

Language selection justification for the bonus implementation.

## Comparison

| Feature | Go | Rust | Java | C# |
|---------|----|----|------|-----|
| **Binary Size** | 7-10 MB | 5-8 MB | 50+ MB | 40+ MB |
| **Compilation** | ⚡ Seconds | 🐌 Minutes | 🐢 Slow | 🐢 Slow |
| **Learning Curve** | Easy | Steep | Medium | Medium |
| **Dependencies** | None | None | JVM | .NET |
| **Cross-compile** | Built-in | Built-in | Complex | Runtime |
| **DevOps Tools** | Docker, K8s, Terraform | Growing | Enterprise | Enterprise |

## Why Go Wins

### 1. Zero Dependencies
```bash
# Go - Single binary
./devops-info-service

# Others need runtime installed
python3 app.py    # Needs Python + packages
java -jar app.jar # Needs JVM
```

### 2. Fast Compilation
```bash
go build main.go  # 1-2 seconds
cargo build       # 30-60 seconds first time
```

### 3. Built-in HTTP Server
```go
// Standard library - no frameworks needed
http.HandleFunc("/", handler)
http.ListenAndServe(":8080", nil)
```

### 5. Cross-Platform Builds
```bash
GOOS=linux GOARCH=amd64 go build    # Linux
GOOS=windows GOARCH=amd64 go build  # Windows  
GOOS=darwin GOARCH=arm64 go build   # macOS M1
```

## Performance

**Startup Time:**
- Go: ~5ms
- Rust: ~3ms
- Python: ~500ms
- Java: ~2000ms

**Memory Usage:**
- Go: ~10 MB
- Rust: ~8 MB
- Python: ~50 MB
- Java: ~120 MB

**Request Latency:**
- Go: ~0.5ms
- Rust: ~0.4ms
- Python: ~2ms
- Java: ~1ms

