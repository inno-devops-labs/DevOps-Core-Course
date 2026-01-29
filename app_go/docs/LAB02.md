# Lab 2 — Multi-Stage Build (Go App)

This document explains the multi-stage containerization of the Go version of the DevOps Info Service, why multi-stage matters, image size comparisons, and technical details.

---

## Strategy Overview

- **Stage 1 (Builder)**: Use `golang:1.22-alpine` to compile a static Linux binary with `CGO_ENABLED=0`, `-trimpath`, and stripped symbols (`-ldflags "-s -w"`). Cache Go modules and build artifacts to speed up incremental builds.
- **Stage 2 (Runtime)**: Use `gcr.io/distroless/static:nonroot` to ship only the binary. No package manager, no shell, and runs as non-root by default → minimal attack surface.

### Dockerfile (multi-stage)
```dockerfile
# ---- Builder stage ----
FROM golang:1.22-alpine AS builder
WORKDIR /src
COPY go.mod ./
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    go mod download
COPY . .
RUN --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
    go build -trimpath -ldflags="-s -w" -buildvcs=false -o /out/app ./main.go

# ---- Runtime stage ----
FROM gcr.io/distroless/static:nonroot
WORKDIR /app
COPY --from=builder /out/app /app/app
USER nonroot:nonroot
EXPOSE 5000
ENV HOST=0.0.0.0 PORT=5000 DEBUG=false
ENTRYPOINT ["/app/app"]
```

---

## Size Comparison

Build both images and compare:
```bash
# build
docker build -t ${DOCKER_USER}/devops-info-service-go:lab02 ./app_go

# check sizes
docker images | grep devops-info-service-go
```

- **Builder image base**: `golang:1.22-alpine` (hundreds of MB, includes toolchain)
- **Final runtime image**: `distroless/static:nonroot` + your binary (typically under ~20MB for small Go services)
- **Observation**: Multi-stage removes compilers and build tools from the final image → significant shrink.

Paste actual output here:
```text
<docker images output>
```

---

## Why Multi-Stage Matters

- **Smaller images**: Faster pulls/pushes and less disk/memory footprint.
- **Security**: Fewer components → fewer CVEs and reduced attack surface; distroless has no shell or package manager.
- **Performance & Deployability**: Static binaries start quickly and work consistently across environments.
- **Best practice**: Keep build-time and runtime concerns separate.

---

## Build & Run Process

### Build
```bash
docker build -t ${DOCKER_USER}/devops-info-service-go:${TAG} ./app_go
```

### Run
```bash
docker run --rm \
  -p ${HOST_PORT}:${CONTAINER_PORT} \
  -e HOST=0.0.0.0 -e PORT=${CONTAINER_PORT} -e DEBUG=${DEBUG_FLAG} \
  ${DOCKER_USER}/devops-info-service-go:${TAG}
```

### Test Endpoints
```bash
curl http://localhost:${HOST_PORT}/health
curl http://localhost:${HOST_PORT}/
```

Paste terminal outputs here:
```text
<build logs>
<run logs>
<curl outputs>
```

---

## Technical Explanation of Each Stage

- **Builder stage**:
  - `go mod download` with cache mounts speeds up dependency resolution.
  - `CGO_ENABLED=0` produces a fully static binary suitable for `distroless/static`.
  - `-trimpath` removes local path info; `-ldflags "-s -w"` strips symbol/debug info → smaller binary.
  - Output binary at `/out/app` for clean handoff to runtime stage.

- **Runtime stage**:
  - `distroless/static:nonroot` includes just enough to run the binary; no shell or glibc needed for static binaries.
  - Runs as non-root (`USER nonroot:nonroot`) by default.
  - `EXPOSE 5000` documents the port; environment variables allow overrides.

---

## Security Implications

- **Reduced attack surface**: No compilers or package managers in runtime.
- **Least privilege**: Non-root execution in runtime stage.
- **Determinism**: Pinned base images and static linking reduce variability.

---

## Trade-offs and Decisions

- **Static vs dynamic**: Static binaries are portable and simplify runtime images; dynamic linking may be needed for certain libraries (CGO), but increases base requirements.
- **Distroless vs Alpine**: Distroless is smaller and more secure; Alpine offers a shell and package manager (useful for debugging), but larger and more components.

---

## Docker Hub (Optional for Go Bonus)

```bash
docker tag ${DOCKER_USER}/devops-info-service-go:${TAG} ${DOCKER_USER}/devops-info-service-go:latest
docker push ${DOCKER_USER}/devops-info-service-go:${TAG}
docker push ${DOCKER_USER}/devops-info-service-go:latest
```

Repo URL pattern:
- `https://hub.docker.com/r/${DOCKER_USER}/devops-info-service-go`
