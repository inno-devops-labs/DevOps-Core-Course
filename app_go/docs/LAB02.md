# Lab 02 — Docker Containerization (Go)

## Multi-Stage Build Strategy

The Go Dockerfile uses two stages:

### Stage 1: Builder

```dockerfile
FROM golang:1.21-alpine AS builder
WORKDIR /build
COPY go.mod .
COPY main.go .
RUN CGO_ENABLED=0 GOOS=linux go build -o devops-info-service
```

**Purpose:** Compile the Go source into a static binary. The `golang:1.21-alpine` image includes the full Go toolchain (~300 MB). `CGO_ENABLED=0` produces a fully static binary with no C library dependencies, which is required to run on `scratch`.

### Stage 2: Runtime

```dockerfile
FROM scratch
COPY --from=builder /build/devops-info-service /devops-info-service
EXPOSE 8080
ENTRYPOINT ["/devops-info-service"]
```

**Purpose:** The final image starts from `scratch` — literally an empty filesystem. Only the compiled binary is copied in. No shell, no package manager, no OS — just the executable.

## Size Comparison

| Image                  | Size     |
|------------------------|----------|
| golang:1.21-alpine     | ~300 MB  |
| Final image (scratch)  | ~7 MB    |
| Python (3.13-slim)     | ~170 MB  |

The multi-stage build reduces the image from ~300 MB (builder) to ~7 MB (final) — a **97% reduction**.

## Why Multi-Stage Builds Matter

**Without multi-stage:** The final image includes the entire Go SDK, build tools, source code, and intermediate build artifacts. This wastes disk space and increases the attack surface.

**With multi-stage:** The final image contains only the compiled binary. There is nothing else to exploit — no shell to exec into, no package manager to install tools, no OS libraries with CVEs.

## Security Benefits

- **`FROM scratch`** — the image has zero packages, zero CVEs by definition. There is literally nothing to patch.
- **No shell** — an attacker cannot `docker exec` into the container and run commands.
- **Static binary** — no dynamic library dependencies that could be exploited.
- **Minimal attack surface** — the only thing running is the application binary.

## Build & Run

```bash
cd app_go
docker build -t devops-info-service-go .
docker run -p 8080:8080 devops-info-service-go
```

## Testing

```bash
curl http://localhost:8080/
curl http://localhost:8080/health
```

## Challenges & Solutions

1. **`scratch` has no CA certificates** — if the app needed HTTPS outbound calls, `scratch` would fail. For this service it's not needed, but for production apps you'd either copy certs from the builder stage or use `gcr.io/distroless/static` instead.
2. **Static compilation required** — `CGO_ENABLED=0` is mandatory for `scratch`. Without it, the binary dynamically links glibc, which doesn't exist in `scratch`.
