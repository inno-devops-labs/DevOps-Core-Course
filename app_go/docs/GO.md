# Language justification

## Why Go
Go was selected as the implementation language because it offers a strong trade-off for a small, container-oriented HTTP JSON service:
- **Fast implementation**: minimal boilerplate, straightforward concurrency model, and a simple standard toolchain.
- **Standard library coverage**: `net/http`, `encoding/json`, `os`, `runtime`, and `time` are sufficient to implement routing, JSON serialization, environment-based configuration, and uptime without external dependencies.
- **Deployment simplicity**: produces a single static-like executable (depending on build settings), integrates cleanly with Docker/Kubernetes, and favors stdout logging by default.
- **Low operational overhead**: fast startup time and modest memory footprint, which is well-suited for health checks and probe endpoints.
- **Portability**: cross-compilation is first-class and enables easy builds for common targets (e.g., Linux/amd64) from a single development environment.

## Contrast with other compiled languages

### Go vs Rust
Rust provides stronger compile-time guarantees around memory safety, but typically increases development complexity (ownership model, lifetimes) and build friction for small services. For this lab-scale HTTP JSON service, Go achieves the required functionality faster while remaining reliable and maintainable.

### Go vs Java
Java commonly implies a JVM/JRE runtime plus build tooling (Maven/Gradle), which increases packaging complexity and container footprint relative to a single Go binary. For a small service intended for probes/monitoring, Go keeps runtime requirements and deployment steps minimal.

### Go vs C/C++
C/C++ can produce small binaries, but requires manual memory management and often more complex build configuration. Go reduces the likelihood of memory-related defects and simplifies maintenance while still providing compiled performance and simple distribution.

## Trade-offs
- Go provides fewer compile-time memory safety guarantees than Rust.
- Implementing routing/middleware without a third-party framework can require more manual code (though the standard library remains sufficient for the scope of this service).

## Summary
Go was chosen to minimize dependencies and operational complexity while delivering a compact, portable HTTP JSON service suitable for containerized environments. Compared to Rust, Java, and C/C++, Go reduces implementation and deployment overhead for this specific lab task, with trade-offs that are acceptable given the service’s limited scope and reliance on the standard library.

