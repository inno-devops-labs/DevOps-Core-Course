# Lab 2 — Bonus: Go Multi‑Stage Docker Build Report

**Student:** Danil Fishchenko  
**Date:** January 31, 2026  
**App:** DevOps Info Service (Go)  
**Multi‑stage:** golang:1.21-alpine → gcr.io/distroless/static:nonroot  

---

## 1. Multi‑Stage Build Strategy

### Stage 1 — Builder
- Uses `golang:1.21-alpine` with Go toolchain
- Downloads modules and compiles a static Linux binary

```dockerfile
FROM golang:1.21-alpine AS builder
WORKDIR /src
COPY go.mod ./
RUN go mod download
COPY main.go ./
RUN CGO_ENABLED=0 GOOS=linux go build -o devops-info-service main.go
```

### Stage 2 — Runtime
- Uses `gcr.io/distroless/static:nonroot`
- Contains only the compiled binary
- Runs as non‑root user

```dockerfile
FROM gcr.io/distroless/static:nonroot
WORKDIR /app
COPY --from=builder /src/devops-info-service /app/devops-info-service
EXPOSE 8080
USER nonroot
ENTRYPOINT ["/app/devops-info-service"]
```

**Why multi‑stage matters:** The builder image includes the entire Go toolchain, while the runtime image only ships the single binary → much smaller final image and reduced attack surface.

---

## 2. Size Comparison (Builder vs Final)

```
devops-info-go:builder  427MB  bb90e6cc92f6
devops-info-go:lab02    16.7MB db3ca225b723
```

**Result:** ~410MB size reduction.

---

## 3. Build & Run Evidence

### Builder stage build

```
[+] Building 8.0s (12/12) FINISHED                  docker:desktop-linux
 => [internal] load build definition from Dockerfile                0.0s
 => => transferring dockerfile: 402B                                0.0s
 => [internal] load metadata for docker.io/library/golang:1.21-alp  0.1s
 => [internal] load .dockerignore                                   0.0s
 => => transferring context: 150B                                   0.0s
 => CACHED [builder 1/6] FROM docker.io/library/golang:1.21-alpine  2.4s
 => => resolve docker.io/library/golang:1.21-alpine@sha256:2414035  2.4s
 => [internal] load build context                                   0.0s
 => => transferring context: 6.68kB                                 0.0s
 => [auth] library/golang:pull token for registry-1.docker.io       0.0s
 => [builder 2/6] WORKDIR /src                                      0.0s
 => [builder 3/6] COPY go.mod ./                                    0.0s
 => [builder 4/6] RUN go mod download                               0.1s
 => [builder 5/6] COPY main.go ./                                   0.0s
 => [builder 6/6] RUN CGO_ENABLED=0 GOOS=linux go build -o devops-  3.7s
 => exporting to image                                              1.6s
```

### Final image build

```
[+] Building 5.5s (15/15) FINISHED                  docker:desktop-linux
 => [internal] load build definition from Dockerfile                0.0s
 => => transferring dockerfile: 402B                                0.0s
 => [internal] load metadata for gcr.io/distroless/static:nonroot   2.5s
 => [internal] load metadata for docker.io/library/golang:1.21-alp  0.0s
 => [internal] load .dockerignore                                   0.0s
 => => transferring context: 150B                                   0.0s
 => [builder 1/6] FROM docker.io/library/golang:1.21-alpine@sha256  0.0s
 => [stage-1 1/3] FROM gcr.io/distroless/static:nonroot@sha256:cba  2.7s
 => [internal] load build context                                   0.0s
 => => transferring context: 54B                                    0.0s
 => CACHED [builder 2/6] WORKDIR /src                               0.0s
 => CACHED [builder 3/6] COPY go.mod ./                             0.0s
 => CACHED [builder 4/6] RUN go mod download                        0.0s
 => CACHED [builder 5/6] COPY main.go ./                            0.0s
 => CACHED [builder 6/6] RUN CGO_ENABLED=0 GOOS=linux go build -o   0.0s
 => [stage-1 2/3] WORKDIR /app                                      0.1s
 => [stage-1 3/3] COPY --from=builder /src/devops-info-service /ap  0.0s
 => exporting to image                                              0.2s
```

### Run container output

```
docker run -d --rm -p 8081:8080 --name devops-info-go-lab02 devops-info-go:lab02
e146bfad2744d327efb5377b5b3b571f7a3fe6c3c2ec65898ad17cc9a6d34b20
```

### Endpoint testing output

**GET /**
```
{
    "service": {
        "name": "devops-info-service",
        "version": "1.0.0",
        "description": "DevOps course info service",
        "framework": "Go (http)"
    },
    "system": {
        "hostname": "e146bfad2744",
        "platform": "linux",
        "platform_version": "go1.21.13",
        "architecture": "arm64",
        "cpu_count": 10,
        "go_version": "1.21.13"
    },
    "runtime": {
        "uptime_seconds": 2,
        "uptime_human": "0 hours, 0 minutes",
        "current_time": "2026-01-31T10:39:15.895162627Z",
        "timezone": "UTC"
    },
    "request": {
        "client_ip": "192.168.65.1",
        "user_agent": "curl/8.7.1",
        "method": "GET",
        "path": "/"
    },
    "endpoints": [
        {
            "path": "/",
            "method": "GET",
            "description": "Service and system information"
        },
        {
            "path": "/health",
            "method": "GET",
            "description": "Health check endpoint"
        }
    ]
}
```

**GET /health**
```
{
    "status": "healthy",
    "timestamp": "2026-01-31T10:39:17.969814503Z",
    "uptime_seconds": 4
}
```

---

## 4. Technical Analysis

### Why multi‑stage is critical for Go
The Go compiler and build tools are large; keeping them in the final image would increase size and attack surface. Multi‑stage builds isolate build tools in the builder stage.

### Security benefits
- Distroless runtime removes shell/package managers
- Non‑root user reduces privilege escalation risk
- Minimal filesystem contents → smaller attack surface

### What if we skipped multi‑stage?
The final image would contain the Go toolchain and OS packages, resulting in much larger size and more vulnerabilities.

---

## 5. Challenges & Solutions

**Challenge:** Port 8080 was already in use on the host.  
**Solution:** Mapped container port 8080 to host port 8081 for testing.

---

## 6. Conclusion

Multi‑stage builds reduced the image from **427MB** to **16.7MB**, while keeping the same runtime behavior and endpoints. This demonstrates how compiled apps benefit significantly from multi‑stage Dockerfiles.