# Go — Language Justification

## Why Go for this service

- **Small, static binaries** — Single executable, no runtime or interpreter. Ideal for Docker multi-stage builds (Lab 2) and minimal images (`scratch` / `alpine`).
- **Fast compilation** — `go build` completes in seconds. Good for CI/CD.
- **Standard library** — `net/http`, `encoding/json`, `os`, `runtime` cover everything we need. No external dependencies.
- **Simple concurrency** — Goroutines and channels are available if we add more workloads later; for this lab, a single handler is enough.
- **Tooling** — `go build`, `go test`, `go mod` are built-in and straightforward.

## Compared to alternatives

| Criterion        | Go       | Rust        | Java/Spring Boot | C# / ASP.NET Core |
|------------------|----------|-------------|------------------|-------------------|
| Binary size      | ~5–8 MB  | Similar     | Large (JVM)      | Large (.NET)      |
| Build speed      | Very fast| Slower      | Moderate         | Moderate          |
| Learning curve   | Low      | Steep       | Moderate         | Moderate          |
| Stdlib HTTP      | Yes      | Via crates  | Via framework    | Via framework     |
| Lab 2 Docker fit | Excellent| Good        | Heavier          | Heavier           |

Go is a good fit for a small HTTP service that will be containerized and used in CI/CD and Kubernetes later in the course.
