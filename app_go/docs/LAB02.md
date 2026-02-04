# LAB02 - Multi-Stage Docker Build (app_go)

## 1. Multi-Stage Build Strategy

- **Builder stage** (`golang:1.21-alpine`): full Go toolchain used to compile a statically-linked binary (`CGO_ENABLED=0`) and strip symbols (`-ldflags='-s -w'`).
- **Final stage** (`scratch`): copies only the compiled binary into an empty image, resulting in a minimal final image with no build tools or package manager.

Why multi-stage:
- Separates build-time dependencies from runtime, keeping final image very small and secure.

Relevant Dockerfile snippet:

```dockerfile
# Builder
FROM golang:1.21-alpine AS builder
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags='-s -w' -o /out/devops-info-service ./

# Final
FROM scratch
COPY --from=builder /out/devops-info-service /usr/local/bin/devops-info-service
EXPOSE 8080
USER 1000
ENTRYPOINT ["/usr/local/bin/devops-info-service"]
```

---

## 2. Build & Run (evidence)

### Build command
```bash
docker build -t <your-username>/devops-info-service:go-lab02 -f app_go/Dockerfile app_go/
```

### Build output
```bash
docker build -t alsstarikova/devops-info-service:go-lab02 -f app_go/Dockerfile app_go/
[+] Building 0.0s (0/0)  docker:[+] Building 0.0s (0/0)  docker:[+] Building 0.0s (0/0)  docker:[+] Building 0.0s (0/1)  docker:[+] Building 0.2s (1/2)  docker:[+] Building 0.3s (1/2)  docker:[+] Building 0.5s (1/2)  docker:[+] Building 0.6s (1/2)  docker:[+] Building 0.8s (1/2)  docker:[+] Building 0.9s (1/2)  docker:[+] Building 1.0s (2/2)  docker:[+] Building 1.1s (3/11)  docker[+] Building 1.3s (4/11)  docker[+] Building 1.5s (4/11)  docker[+] Building 1.7s (4/11)  docker[+] Building 1.8s (4/11)  docker[+] Building 2.0s (4/11)  docker[+] Building 2.1s (4/11)  docker[+] Building 2.3s (4/11)  docker[+] Building 2.4s (4/11)  docker[+] Building 2.5s (4/11)  docker[+] Building 2.7s (4/11)  docker[+] Building 2.8s (4/11)  docker[+] Building 2.9s (4/11)  docker[+] Building 3.1s (4/11)  docker[+] Building 3.2s (4/11)  docker[+] Building 3.4s (4/11)  docker[+] Building 3.6s (4/11)  docker[+] Building 3.8s (4/11)  docker[+] Building 3.9s (4/11)  docker[+] Building 4.0s (4/11)  docker[+] Building 4.1s (4/11)  docker[+] Building 4.3s (4/11)  docker[+] Building 4.5s (4/11)  docker[+] Building 4.6s (4/11)  docker[+] Building 4.8s (4/11)  docker[+] Building 4.9s (4/11)  docker[+] Building 5.1s (4/11)  docker[+] Building 5.2s (4/11)  docker[+] Building 5.3s (4/11)  docker[+] Building 5.5s (4/11)  docker[+] Building 5.7s (4/11)  docker[+] Building 5.8s (4/11)  docker[+] Building 5.9s (4/11)  docker[+] Building 6.1s (4/11)  docker[+] Building 6.3s (4/11)  docker[+] Building 6.5s (4/11)  docker[+] Building 6.7s (4/11)  docker[+] Building 6.9s (4/11)  docker[+] Building 7.1s (4/11)  docker[+] Building 7.2s (4/11)  docker[+] Building 7.3s (4/11)  docker[+] Building 7.4s (4/11)  docker[+] Building 7.5s (4/11)  docker[+] Building 7.6s (4/11)  docker[+] Building 7.8s (4/11)  docker[+] Building 7.9s (4/11)  docker[+] Building 8.0s (4/11)  docker[+] Building 8.2s (4/11)  docker[+] Building 8.2s (4/11)  docker[+] Building 8.3s (4/11)  docker[+] Building 8.4s (4/11)  docker[+] Building 8.6s (4/11)  docker[+] Building 8.7s (4/11)  docker[+] Building 8.9s (4/11)  docker[+] Building 9.0s (4/11)  docker[+] Building 9.1s (4/11)  docker[+] Building 9.2s (4/11)  docker[+] Building 9.3s (4/11)  docker[+] Building 9.4s (4/11)  docker[+] Building 9.4s (4/11)  docker[+] Building 9.6s (4/11)  docker[+] Building 9.7s (4/11)  docker[+] Building 9.8s (4/11)  docker[+] Building 10.0s (4/11)  docke[+] Building 10.1s (4/11)  docke[+] Building 10.3s (4/11)  docke[+] Building 10.3s (4/11)  docke[+] Building 10.4s (4/11)  docke[+] Building 10.5s (4/11)  docke[+] Building 10.7s (5/11)  docke[+] Building 10.7s (6/11)  docke[+] Building 10.9s (7/11)  docke[+] Building 11.0s (7/11)  docke[+] Building 11.2s (9/11)  docke[+] Building 11.3s (9/11)  docke[+] Building 11.5s (9/11)  docke[+] Building 11.6s (9/11)  docke[+] Building 11.8s (9/11)  docke[+] Building 11.9s (9/11)  docke[+] Building 12.1s (9/11)  docke[+] Building 12.2s (9/11)  docke[+] Building 12.4s (9/11)  docke[+] Building 12.5s (9/11)  docke[+] Building 12.7s (9/11)  docke[+] Building 12.8s (9/11)  docke[+] Building 13.0s (9/11)  docke[+] Building 13.1s (9/11)  docke[+] Building 13.3s (9/11)  docke[+] Building 13.4s (9/11)  docke[+] Building 13.6s (9/11)  docke[+] Building 13.7s (9/11)  docke[+] Building 13.9s (9/11)  docke[+] Building 14.0s (9/11)  docke[+] Building 14.2s (9/11)  docke[+] Building 14.3s (9/11)  docke[+] Building 14.5s (9/11)  docke[+] Building 14.6s (9/11)  docke[+] Building 14.8s (9/11)  docke[+] Building 14.9s (9/11)  docke[+] Building 15.1s (9/11)  docke[+] Building 15.2s (9/11)  docke[+] Building 15.4s (9/11)  docke[+] Building 15.5s (9/11)  docke[+] Building 15.6s (10/11)  dock[+] Building 15.6s (12/12) FINISHED docker:defaultsha256:  0.1s
 => [internal] load build  0.0s
 => => transferring  808B  0.0s
 => [internal] load metad  1.0s
 => [internal] load .dock  0.0s
 => => transferring co 2B  0.0s
 => [builder 1/6] FROM do  9.4s
 => => resolve docker.io/  0.0s
 => => extracting sha256:  0.1s
 => => extracting sha256:  0.0s
 => => extracting sha256:  3.1s
 => => extracting sha256:  0.0s
 => => extracting sha256:  0.0s
 => [internal] load build  0.1s
 => => transferrin 1.24kB  0.1s
 => [builder 2/6] WORKDIR  0.2s
 => [builder 3/6] COPY go  0.0s
 => [builder 4/6] RUN go   0.2s
 => [builder 5/6] COPY .   0.0s
 => [builder 6/6] RUN CGO  4.6s
 => [stage-1 1/1] COPY --  0.0s
 => exporting to image     0.0s
 => => exporting layers    0.0s
 => => writing image sha2  0.0s
 => => naming to docker.i  0.0s
```

### Run command
```bash
docker run --rm -p 8080:8080 <your-username>/devops-info-service:go-lab02
```

### Run output (paste below)
```bash
docker run -d --rm -p 8080:8080 --name dev-go-test alsstarikova/devops-info-service:go-lab02
8c96a3e66cb22e706526764e90699a0ac7b33f619ea8d773f54bedc1ea75e16e
```

### Test endpoint (curl)
```bash
curl -sS http://localhost:8080/health | jq .
```

### Test output (paste below)
```bash
curl -sS http://l
ocalhost:8080/health | jq .
{
  "status": "healthy",
  "timestamp": "2026-02-04T18:41:46Z",
  "uptime_seconds": 21
}
alenaprogramming1@LAPTOP-LJVRUS9G:My_Py_Projects/DevOps-Core-Course ‹lab02*›$  curl -sS http://l
ocalhost:8080/ | jq .
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Go net/http"
  },
  "system": {
    "hostname": "8c96a3e66cb2",
    "platform": "linux",
    "platform_version": "amd64",
    "architecture": "amd64",
    "cpu_count": 20,
    "go_version": "go1.21.13"
  },
  "runtime": {
    "uptime_seconds": 30,
    "uptime_human": "0 hours, 0 minutes",
    "current_time": "2026-02-04T18:41:56Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "172.17.0.1:35896",
    "user_agent": "curl/7.81.0",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {
      "description": "Service information",
      "method": "GET",
      "path": "/"
    },
    {
      "description": "Health check",
      "method": "GET",
      "path": "/health"
    }
  ]
}
```

---

## 3. Size comparison & analysis

- **Final image size (measured)**: `4.71MB` (measured with `docker images`)

**Assessment:** The final image is significantly smaller than any full SDK-based image because it contains only a single statically-linked binary. This reduces network transfer and attack surface.

Commands used to measure sizes:
- `docker images --format "{{.Repository}}:{{.Tag}} {{.Size}}"`
- `docker history --no-trunc <image>`

```bash
docker images --format "{{.Repository}}:{{.Tag}} 
{{.Size}}"
alsstarikova/devops-info-service:go-lab02 4.71MB
```

---

## 4. Technical explanation

- Building with `CGO_ENABLED=0` produces a static binary so it can be run in `scratch` with no additional runtime libraries.
- Stripping symbols (`-s -w`) reduces binary size.
- Using a numeric `USER` in the final stage avoids running as root while not depending on `/etc/passwd` in `scratch`.

