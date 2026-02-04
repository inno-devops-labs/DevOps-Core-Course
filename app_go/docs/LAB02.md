# LAB02 (Bonus) — Multi-Stage Docker Build (Go)

This document explains how I containerized the compiled Go application using a **multi-stage Docker build** to minimize the final image size and reduce the runtime attack surface. 

---

## Multi-Stage Strategy

### Stage 1 — Builder

- **Image:** `golang:1.23.5-alpine3.21`
    
- **Purpose:** provides the Go toolchain needed to compile the application.
    
- **Output artifact:** a single Linux binary at `/out/devops-info-service`.
    

Key choices and why they matter:

- **Dependency caching:** `go mod download` runs right after copying `go.mod`, before copying source code.  
    This means dependency download is cached and not repeated on every code change.
    
- **Static binary:** `CGO_ENABLED=0` builds a static binary, which makes it suitable for minimal runtime images.
    
- **Smaller binary:** `-ldflags="-s -w"` strips debug symbols to reduce binary size.
    

### Stage 2 — Runtime

- **Image:** `gcr.io/distroless/static-debian12:nonroot`
    
- **Purpose:** run only the binary (no shell, no package manager, minimal filesystem).
    
- **Security benefit:** default **non-root** user and fewer components installed → smaller attack surface.
    

---

## Size Comparison (builder vs final)

Final image size from `docker images`:

```
REPOSITORY        TAG      IMAGE ID       CREATED         SIZE
lab02-go          latest   0f3bc22c104c   2 minutes ago   13.4MB
lab02-go-builder  latest   a52c4160b20d   2 minutes ago   468MB
```


**Analysis:**  
The multi-stage Go image is much smaller because the final runtime stage contains only the compiled binary and a minimal runtime filesystem. The builder stage contains the full Go toolchain and is not shipped.

---

## Dockerfile Walkthrough

Key parts of the Dockerfile and purpose:

```dockerfile
FROM golang:1.23.5-alpine3.21 AS builder
WORKDIR /src

COPY go.mod ./
RUN go mod download
```

- Copies only `go.mod` first and downloads dependencies → maximizes Docker layer caching.
    

```dockerfile
COPY main.go ./

ARG TARGETOS
ARG TARGETARCH

RUN CGO_ENABLED=0 GOOS=${TARGETOS:-linux} GOARCH=${TARGETARCH:-arm64} \
    go build -trimpath -ldflags="-s -w" -o /out/devops-info-service .
```

- Copies the source and compiles a **static** binary.
    
- Uses `TARGETOS/TARGETARCH` to build correctly on different platforms (important on Apple Silicon / arm64).
    

```dockerfile
FROM gcr.io/distroless/static-debian12:nonroot AS runtime
WORKDIR /app
COPY --from=builder /out/devops-info-service /app/devops-info-service
EXPOSE 8080 ENV HOST=0.0.0.0 PORT=8080
ENTRYPOINT ["/app/devops-info-service"]
```

- Distroless runtime is minimal and runs as non-root.
    
- Only the binary is copied into the final image.
    
- Port and env vars match the app defaults.
    

---

## Build & Run Evidence

### Build

```shell
docker build -t lab02-go -f app_go/Dockerfile app_go [+]
Building ... FINISHED
=> naming to docker.io/library/lab02-go:latest
```

### Run

```shell
docker run --rm -p 8080:8080 lab02-go
```

### Test endpoints

```shell
curl http://localhost:8080/
# returned JSON with service/system/runtime/request information
```

(Optionally)

```shell
curl http://localhost:8080/health
```

---

## Why Multi-Stage Builds Matter (Compiled Languages)

- **Smaller images:** faster pulls, less storage, faster deploys (final image is ~13.4MB).
    
- **Security:** runtime image excludes compilers, shells, package managers → fewer vulnerabilities and lower attack surface.
    
- **Clear separation:** build-time vs run-time concerns are isolated.
    

Trade-offs:

- Dockerfile becomes slightly more complex.
    
- Debugging inside distroless containers is harder (no shell), so logs/metrics are preferred.