# Lab 2 — Multi-Stage Docker Build (Go)

## Multi-Stage Build Strategy

### Overview

Multi-stage builds allow us to separate the build environment from the runtime environment, resulting in minimal production images.

```
┌─────────────────────────────────────────────────────────────┐
│ Stage 1: Builder (golang:1.22-alpine)                       │
│   • Full Go SDK (~400MB)                                    │
│   • Compiles source code                                    │
│   • Creates static binary                                   │
└────────────────────────┬────────────────────────────────────┘
                         │ COPY binary only
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Stage 2: Runtime (alpine:3.19)                              │
│   • Minimal base (~7MB)                                     │
│   • Only the compiled binary                                │
│   • Non-root user                                           │
└─────────────────────────────────────────────────────────────┘
```

### Dockerfile Explained

```dockerfile
# Stage 1: Builder - Compile the application
FROM golang:1.22-alpine AS builder
WORKDIR /build
COPY go.mod main.go ./
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -ldflags="-s -w" \
    -o devops-info-service .
```

**Key decisions:**
- `CGO_ENABLED=0`: Creates a static binary without C dependencies
- `-ldflags="-s -w"`: Strips debug symbols and DWARF info for smaller binary
- `GOOS=linux GOARCH=amd64`: Cross-compilation for Linux

```dockerfile
# Stage 2: Runtime - Minimal production image
FROM alpine:3.19
RUN adduser -u 1000 -G appgroup -s /bin/sh -D appuser
COPY --from=builder /build/devops-info-service .
USER appuser
CMD ["./devops-info-service"]
```

**Key decisions:**
- `alpine:3.19`: Tiny base image (~7MB)
- Non-root user for security
- Only the binary is copied from builder

---

## Size Comparison

| Image | Size | Purpose |
|-------|------|---------|
| golang:1.22-alpine (builder) | ~400MB | Full Go SDK |
| **devops-info-service:go (final)** | **17.8MB** | Production runtime |
| devops-info-service:python | 157MB | Python version |

### Size Reduction Analysis

```
Builder stage:     ~400MB (Go SDK + tools)
                      ↓
Final image:        17.8MB
                      ↓
Reduction:         95.5% smaller than builder
                   89% smaller than Python version
```

**Why this matters:**
- **Faster deployments:** Smaller images pull faster
- **Reduced storage costs:** Less disk space needed
- **Smaller attack surface:** Fewer packages = fewer vulnerabilities

---

## Build Process Output

```
$ docker build -t devops-info-service:go .

[+] Building 45.1s (13/13) FINISHED
 => [builder 1/6] FROM docker.io/library/golang:1.22-alpine
 => [builder 2/6] RUN apk add --no-cache git
 => [builder 3/6] WORKDIR /build
 => [builder 4/6] COPY go.mod ./
 => [builder 5/6] COPY main.go .
 => [builder 6/6] RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags="-s -w" -o devops-info-service .
 => [stage-1 1/6] FROM docker.io/library/alpine:3.19
 => [stage-1 2/6] RUN apk --no-cache add ca-certificates
 => [stage-1 3/6] RUN addgroup -g 1000 appgroup && adduser -u 1000 -G appgroup -s /bin/sh -D appuser
 => [stage-1 4/6] WORKDIR /app
 => [stage-1 5/6] COPY --from=builder /build/devops-info-service .
 => [stage-1 6/6] RUN chown -R appuser:appgroup /app
 => exporting to image
 => => naming to docker.io/library/devops-info-service:go
```

### Container Testing

```
$ docker run -d -p 8080:8080 --name test-go devops-info-service:go
631cf4d872808c34da6ca175fb099ec500283b375ecf02f965b432c28a4aeb3b

$ curl http://localhost:8080/
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"net/http"},"system":{"hostname":"631cf4d87280","platform":"linux","platform_version":"linux/amd64","architecture":"amd64","cpu_count":12,"go_version":"go1.22.12"},...}

$ curl http://localhost:8080/health
{"status":"healthy","timestamp":"2026-02-04T17:53:42Z","uptime_seconds":2}

$ docker exec test-go whoami
appuser
```

### Image Sizes

```
$ docker images | grep devops-info-service
devops-info-service   go       68f2cdfb037b   17.8MB
devops-info-service   python   6ac4159bcb60   157MB
```

---

## Technical Analysis

### Why Multi-Stage Builds Matter for Compiled Languages

Without multi-stage builds:
```dockerfile
# BAD - Final image includes entire Go SDK
FROM golang:1.22-alpine
COPY . .
RUN go build -o app .
CMD ["./app"]
# Result: ~400MB image with compiler, tools, source code
```

With multi-stage builds:
```dockerfile
# GOOD - Final image only has binary
FROM golang:1.22-alpine AS builder
RUN go build -o app .

FROM alpine:3.19
COPY --from=builder /build/app .
CMD ["./app"]
# Result: ~18MB image with only the binary
```

### Security Benefits

| Benefit | Explanation |
|---------|-------------|
| Smaller attack surface | No compiler, no package managers, no source code |
| Fewer CVEs | Alpine has ~10 packages vs ~200 in full images |
| Non-root execution | Limited privilege if compromised |
| No build artifacts | Source code not exposed in production |

### Static Binary Advantages

```bash
CGO_ENABLED=0 go build -o app
```

- **No runtime dependencies:** Binary runs standalone
- **Works on `scratch`:** Could use empty base image (0 bytes)
- **Portable:** Same binary works on any Linux
- **Chose Alpine:** Added ca-certificates for HTTPS, wget for healthcheck

---

## Why 17.8MB and Not Smaller?

Final image breakdown:
- Alpine base: ~7MB
- ca-certificates: ~1MB
- Go binary: ~9MB
- User/group files: <1KB

**Could go smaller with:**
- `FROM scratch`: 0 bytes base, but no shell, no healthcheck tools
- UPX compression: Compresses binary but slower startup
- Distroless: ~2MB base but more complex debugging

**Chose Alpine for:** 
- Shell access for debugging
- wget for healthcheck
- ca-certificates already available
