# LAB02 - Docker Containerization (Go, Multi-Stage)

## Multi-Stage Build Strategy
I used a two-stage Dockerfile:
1. **Builder stage** (`golang:1.22`) to compile the binary.
2. **Runtime stage** (`distroless/static-debian12:nonroot`) to run only the binary.

This keeps the final image small and removes the Go toolchain from production.

Dockerfile snippet:
```dockerfile
FROM golang:1.22 AS builder
WORKDIR /src
COPY go.mod ./
RUN go mod download
COPY main.go ./
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o devops-info

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=builder /src/devops-info /app/devops-info
ENTRYPOINT ["/app/devops-info"]
```


Image size output:
```text
tsixphoenix/devops-info-go                    latest            7fc572b1d863   4 minutes ago       17.7MB
```

## Build and Run Evidence
Build output:
```text
docker build -t tsixphoenix/devops-info-go:latest .  
[+] Building 35.3s (16/16) FINISHED                                                                                                                                                      docker:desktop-linux
 => [internal] load build definition from Dockerfile                                                                                                                                                     0.0s
 => => transferring dockerfile: 396B                                                                                                                                                                     0.0s 
 => [internal] load metadata for gcr.io/distroless/static-debian12:nonroot                                                                                                                               1.8s 
 => [internal] load metadata for docker.io/library/golang:1.22                                                                                                                                           2.4s 
 => [auth] library/golang:pull token for registry-1.docker.io                                                                                                                                            0.0s
 => [internal] load .dockerignore                                                                                                                                                                        0.0s
 => => transferring context: 91B                                                                                                                                                                         0.0s 
 => [builder 1/6] FROM docker.io/library/golang:1.22@sha256:1cf6c45ba39db9fd6db16922041d074a63c935556a05c5ccb62d181034df7f02                                                                            22.6s 
 => => resolve docker.io/library/golang:1.22@sha256:1cf6c45ba39db9fd6db16922041d074a63c935556a05c5ccb62d181034df7f02                                                                                     0.0s 
 => => sha256:1451027d3c0ee892b96310c034788bbe22b30b8ea2d075edbd09acfeaaaa439f 126B / 126B                                                                                                               0.4s 
 => => sha256:afa154b433c7f72db064d19e1bcfa84ee196ad29120328f6bdb2c5fbd7b8eeac 69.36MB / 69.36MB                                                                                                         8.8s 
 => => sha256:3b7f19923e1501f025b9459750b20f5df37af452482f75b91205f345d1c0e1b5 92.33MB / 92.33MB                                                                                                        10.0s 
 => => sha256:35af2a7690f2b43e7237d1fae8e3f2350dfb25f3249e9cf65121866f9c56c772 64.39MB / 64.39MB                                                                                                         8.1s 
 => => sha256:32b550be6cb62359a0f3a96bc0dc289f8b45d097eaad275887f163c6780b4108 24.06MB / 24.06MB                                                                                                         3.8s
 => => sha256:a492eee5e55976c7d3feecce4c564aaf6f14fb07fdc5019d06f4154eddc93fde 48.48MB / 48.48MB                                                                                                         5.2s 
 => => extracting sha256:a492eee5e55976c7d3feecce4c564aaf6f14fb07fdc5019d06f4154eddc93fde                                                                                                                2.3s 
 => => extracting sha256:32b550be6cb62359a0f3a96bc0dc289f8b45d097eaad275887f163c6780b4108                                                                                                                0.8s 
 => => extracting sha256:35af2a7690f2b43e7237d1fae8e3f2350dfb25f3249e9cf65121866f9c56c772                                                                                                                2.5s 
 => => extracting sha256:3b7f19923e1501f025b9459750b20f5df37af452482f75b91205f345d1c0e1b5                                                                                                                2.0s
 => => extracting sha256:afa154b433c7f72db064d19e1bcfa84ee196ad29120328f6bdb2c5fbd7b8eeac                                                                                                                5.1s 
 => => extracting sha256:1451027d3c0ee892b96310c034788bbe22b30b8ea2d075edbd09acfeaaaa439f                                                                                                                0.0s 
 => => extracting sha256:4f4fb700ef54461cfa02571ae0db9a0dc1e0cdb5577484a6d75e68dc38e8acc1                                                                                                                0.0s
 => [internal] load build context                                                                                                                                                                        0.1s 
 => => transferring context: 6.51kB                                                                                                                                                                      0.0s 
 => [stage-1 1/3] FROM gcr.io/distroless/static-debian12:nonroot@sha256:cba10d7abd3e203428e86f5b2d7fd5eb7d8987c387864ae4996cf97191b33764                                                                 2.9s 
 => => resolve gcr.io/distroless/static-debian12:nonroot@sha256:cba10d7abd3e203428e86f5b2d7fd5eb7d8987c387864ae4996cf97191b33764                                                                         0.0s
 => => sha256:069d1e267530c2e681fbd4d481553b4d05f98082b18fafac86e7f12996dddd0b 131.91kB / 131.91kB                                                                                                       0.6s
 => => sha256:dcaa5a89b0ccda4b283e16d0b4d0891cd93d5fe05c6798f7806781a6a2d84354 314B / 314B                                                                                                               0.4s 
 => => sha256:4aa0ea1413d37a58615488592a0b827ea4b2e48fa5a77cf707d0e35f025e613f 385B / 385B                                                                                                               0.4s 
 => => sha256:dd64bf2dd177757451a98fcdc999a339c35dee5d9872d8f4dc69c8f3c4dd0112 80B / 80B                                                                                                                 0.4s 
 => => sha256:52630fc75a18675c530ed9eba5f55eca09b03e91bd5bc15307918bbc1a7e7296 162B / 162B                                                                                                               0.3s 
 => => sha256:3214acf345c0cc6bbdb56b698a41ccdefc624a09d6beb0d38b5de0b2303ecaf4 123B / 123B                                                                                                               0.3s 
 => => sha256:7c12895b777bcaa8ccae0605b4de635b68fc32d60fa08f421dc3818bf55ee212 188B / 188B                                                                                                               0.3s 
 => => sha256:2780920e5dbfbe103d03a583ed75345306e572ec5a48cb10361f046767d9f29a 67B / 67B                                                                                                                 0.3s 
 => => sha256:62de241dac5fe19d5f8f4defe034289006ddaa0f2cca735db4718fe2a23e504e 31.24kB / 31.24kB                                                                                                         0.6s 
 => => sha256:017886f7e1764618ffad6fbd503c42a60076c63adc16355cac80f0f311cae4c9 544.07kB / 544.07kB                                                                                                       0.7s 
 => => sha256:bfb59b82a9b65e47d485e53b3e815bca3b3e21a095bd0cb88ced9ac0b48062bf 13.36kB / 13.36kB                                                                                                         0.6s 
 => => sha256:fab8c4b3fa32236a59c44cc504a69b18788d5c17c045691c2d682267ae8cf468 104.22kB / 104.22kB                                                                                                       0.6s 
 => => extracting sha256:fab8c4b3fa32236a59c44cc504a69b18788d5c17c045691c2d682267ae8cf468                                                                                                                0.1s 
 => => extracting sha256:bfb59b82a9b65e47d485e53b3e815bca3b3e21a095bd0cb88ced9ac0b48062bf                                                                                                                0.1s 
 => => extracting sha256:017886f7e1764618ffad6fbd503c42a60076c63adc16355cac80f0f311cae4c9                                                                                                                0.5s 
 => => extracting sha256:62de241dac5fe19d5f8f4defe034289006ddaa0f2cca735db4718fe2a23e504e                                                                                                                0.1s 
 => => extracting sha256:2780920e5dbfbe103d03a583ed75345306e572ec5a48cb10361f046767d9f29a                                                                                                                0.0s 
 => => extracting sha256:7c12895b777bcaa8ccae0605b4de635b68fc32d60fa08f421dc3818bf55ee212                                                                                                                0.0s 
 => => extracting sha256:3214acf345c0cc6bbdb56b698a41ccdefc624a09d6beb0d38b5de0b2303ecaf4                                                                                                                0.1s 
 => => extracting sha256:52630fc75a18675c530ed9eba5f55eca09b03e91bd5bc15307918bbc1a7e7296                                                                                                                0.1s 
 => => extracting sha256:dd64bf2dd177757451a98fcdc999a339c35dee5d9872d8f4dc69c8f3c4dd0112                                                                                                                0.0s 
 => => extracting sha256:4aa0ea1413d37a58615488592a0b827ea4b2e48fa5a77cf707d0e35f025e613f                                                                                                                0.0s 
 => => extracting sha256:dcaa5a89b0ccda4b283e16d0b4d0891cd93d5fe05c6798f7806781a6a2d84354                                                                                                                0.0s 
 => => extracting sha256:069d1e267530c2e681fbd4d481553b4d05f98082b18fafac86e7f12996dddd0b                                                                                                                0.0s 
 => [stage-1 2/3] WORKDIR /app                                                                                                                                                                           0.1s 
 => [builder 2/6] WORKDIR /src                                                                                                                                                                           0.5s 
 => [builder 3/6] COPY go.mod ./                                                                                                                                                                         0.1s 
 => [builder 4/6] RUN go mod download                                                                                                                                                                    0.5s 
 => [builder 5/6] COPY main.go ./                                                                                                                                                                        0.1s 
 => [builder 6/6] RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o devops-info                                                                                                                      8.1s 
 => [stage-1 3/3] COPY --from=builder /src/devops-info /app/devops-info                                                                                                                                  0.1s 
 => exporting to image                                                                                                                                                                                   0.6s 
 => => exporting layers                                                                                                                                                                                  0.4s 
 => => exporting manifest sha256:39177489cedb41b9d9f566a8be5d09c8ffe938f98b590aa0ebb987f1cf38d7a6                                                                                                        0.0s 
 => => exporting config sha256:d86ea6d9a836253c87a0ac2232aa6f03cdc8198146f9acdba1f3d31c617bca82                                                                                                          0.0s 
 => => exporting attestation manifest sha256:79e9867f53966cbf5943864985b72aeed88ea8a8349789577aee72d45045e5af                                                                                            0.0s 
 => => exporting manifest list sha256:7fc572b1d86304a2634962e06610c7cf4295c4a466b6e52aed34f93550555008                                                                                                   0.0s 
 => => naming to docker.io/tsixphoenix/devops-info-go:latest                                                                                                                                             0.0s 
 => => unpacking to docker.io/tsixphoenix/devops-info-go:latest                                                                                                                                          0.1s 

```

Run output:
```text
docker run --rm -p 5000:5000 --name devops-info-go tsixphoenix/devops-info-go:latest  
2026/01/29 12:37:42 Starting DevOps Info Service on 0.0.0.0:5000
```

Endpoint checks:
```text
curl http://localhost:5000/
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"Go net/http"},"system":{"hostname":"50a30efde177","platform":"linux","platform_version":"Distroless","architecture":"amd64","cpu_count":12,"python_version":"go1.22.12"},"runtime":{"uptime_seconds":79,"uptime_human":"0 hours, 1 minute","current_time":"2026-01-29T12:39:02Z","timezone":"UTC"},"request":{"client_ip":"172.17.0.1","user_agent":"curl/8.16.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"}]}

curl http://localhost:5000/health
{"status":"healthy","timestamp":"2026-01-29T12:39:31Z","uptime_seconds":108}

2026/01/29 12:39:02 Request: GET /
2026/01/29 12:39:02 Response: GET / -> 200 (418.191µs)
2026/01/29 12:39:31 Request: GET /health
2026/01/29 12:39:31 Response: GET /health -> 200 (114.664µs)
```

## Technical Analysis
- The builder stage contains the full Go toolchain; the runtime stage does not.
- If I shipped the builder stage, the image would be much larger and include tools that should not be in production.
- A static binary lets me use a minimal base image.
- The final image runs as a non-root user, which reduces risk.

## Challenges and Solutions
- I made sure the binary was static (CGO disabled) so it works in a minimal runtime image.
- Distroless images do not include a shell, so debugging is done in the builder stage, not in the runtime image.
