## LAB02 — Docker Containerization (Go, Bonus)

### Multi-Stage Build Strategy

The Go app is containerized using a **multi-stage Dockerfile** with two stages:

1. **Builder stage** (`golang:1.24-alpine`): Compiles the application.
2. **Runtime stage** (`alpine:3.21`): Runs only the compiled binary.

**Why multi-stage?** The builder image includes the Go compiler, SDK, and build tools (~300 MB). The runtime image needs none of that—just the static binary and a minimal OS. Copying only the binary into Alpine yields an image under 20 MB.

---

### Stage Breakdown

#### Stage 1: Builder

```dockerfile
FROM golang:1.24-alpine AS builder
WORKDIR /build
COPY go.mod .
RUN go mod download
COPY main.go .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o devops-info-service .
```

| Step | Purpose |
|------|---------|
| `go.mod` first | Dependencies are cached when only `main.go` changes |
| `CGO_ENABLED=0` | Produces a static binary with no C dependencies; works on any Linux base |
| `-ldflags="-s -w"` | Strips debug info to reduce binary size |
| `-o devops-info-service` | Single output binary to copy into runtime |

#### Stage 2: Runtime

```dockerfile
FROM alpine:3.21
RUN addgroup -g 1000 appgroup && adduser -D -u 1000 -G appgroup appuser
WORKDIR /app
COPY --from=builder /build/devops-info-service .
RUN chown appuser:appgroup devops-info-service
USER appuser
EXPOSE 5000
ENV PORT=5000 HOST=0.0.0.0
CMD ["./devops-info-service"]
```

| Step | Purpose |
|------|---------|
| `COPY --from=builder` | Copy only the binary from the builder stage |
| Non-root user | Run as `appuser` for security |
| Alpine 3.21 | Small base (~5 MB); static binary needs no C runtime |

---

### Size Comparison

*Replace with your actual output from `docker images`.*

| Image | Size |
|-------|------|
| `golang:1.24-alpine` (builder) | ~300 MB |
| `devops-info-service` (final) | ~15–20 MB |

**Size reduction:** ~95% smaller than using the builder image as the final image.

---

### Why Multi-Stage Matters for Compiled Languages

- **Builder image:** Includes compiler, linker, headers, and libraries. Necessary only for building.
- **Runtime:** Only needs the compiled binary and minimal runtime (Alpine).
- **Security:** Fewer packages and tools reduce attack surface.
- **Deploy speed:** Smaller images pull and start faster.

---

### Build & Run

**Build:**

```bash
cd app_go
docker build -t devops-info-service-go .
```

*Add your actual build output here.*

**Run:**

```bash
docker run -d -p 5000:5000 --name devops-go devops-info-service-go
```

**Test:**

```bash
curl http://localhost:5000/
curl http://localhost:5000/health
```

---

### Security Benefits

- **Non-root user:** Limits damage if the app is compromised.
- **Minimal base:** Alpine has fewer packages than full distros.
- **Static binary:** No runtime dependency installation; fewer paths for supply-chain issues.
- **Smaller image:** Less code to audit and fewer CVE-prone components.
