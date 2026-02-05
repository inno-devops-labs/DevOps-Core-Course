# LAB02 — Multi-stage Docker build for Go (English)

Date: 2026-02-05

Goal: demonstrate a multi-stage Docker build for the Go application and explain decisions, trade-offs and measurements.

## Multi-stage build strategy

- **Builder stage (golang:1.22-alpine)** — compiles a statically linked binary with `CGO_ENABLED=0` and `-ldflags "-s -w"` to strip debugging symbols.
- **Runtime stage (scratch)** — copies only the resulting binary from the builder (`COPY --from=builder`) into a minimal image with no package manager or shell.

Why this matters:
- The builder image contains compilers, source and toolchain (large). The final image contains only the binary, dramatically reducing size and attack surface.
- `COPY --from=builder` pulls artifacts from the named build stage into the final image.

Dockerfile excerpts:

```dockerfile
FROM golang:1.22-alpine AS builder
WORKDIR /src
COPY go.mod ./
RUN apk add --no-cache git && go mod tidy
COPY . .
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags "-s -w" -o /devops-info ./

FROM scratch
COPY --from=builder /devops-info /devops-info
EXPOSE 5002
USER 1000
ENTRYPOINT ["/devops-info"]
```

Notes:
- `CGO_ENABLED=0` ensures a static binary that can run in `scratch` (no libc present). If the app uses C bindings, static build may fail and a different runtime base (e.g., distroless) may be required.
- We set `GOARCH=amd64` to produce an amd64 binary; adjust for your target architecture if needed (e.g., `arm64`).

## Build & size measurements

Commands executed locally (captured output below):

```bash
docker build --platform=linux/amd64 -t devops-go:lab2 app_go
docker build --platform=linux/amd64 --target builder -t devops-go:builder app_go
docker images devops-go:lab2 --format "{{.Repository}}:{{.Tag}} {{.Size}}"
docker images devops-go:builder --format "{{.Repository}}:{{.Tag}} {{.Size}}"
```

Key terminal output (build & sizes):

```
... (build output omitted) ...
devops-go:lab2 2.16MB
devops-go:builder 103MB
```

Analysis:
- **Builder image (103MB)**: includes the Go toolchain and apk packages required to fetch dependencies and build the binary.
- **Final image (2.16MB)**: contains only the stripped static binary — well under the 20MB challenge target.

Why you can't use the builder image as the final image:
- The builder contains compilers and package managers which increase image size and add additional attack surface. Keeping build tools out of production images reduces risk and distribution size.

Security implications:
- Smaller images have fewer packages and fewer potential vulnerabilities.
- `scratch` has no shell; if an attacker gains code execution they have very limited tooling.
- Running as a non-root numeric user (`USER 1000`) reduces privilege even further.

Trade-offs and notes:
- Using `scratch` gives the smallest possible image but also removes diagnostic tools; debugging requires reproducing the builder environment or adding temporary debug builds.
- If the binary depends on cgo or system libs, `scratch` may be unsuitable; use a minimal distro or distroless image.

## Technical explanation of each stage

- Builder stage:
  - Installs `git` to allow `go mod tidy` to fetch modules.
  - Copies `go.mod`, runs `go mod tidy` to populate `go.sum` and download dependencies (cached when `go.mod` hasn't changed).
  - Copies source and builds a static binary with optimizations and stripped symbols.

- Final stage:
  - Uses `scratch` for minimal footprint.
  - Copies only the binary.
  - Exposes the application port and runs the binary directly.

## Terminal outputs (selected)

Build final image (abridged):

```
#10 [builder 6/6] RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64     go build -ldflags "-s -w" -o /devops-info ./
#12 exporting to image
#12 naming to docker.io/library/devops-go:lab2 done
```

Image sizes:

```
devops-go:lab2 2.16MB
devops-go:builder 103MB
```

## Conclusion

The multi-stage build achieved a very small runtime image (2.16MB) by compiling a static Go binary and copying only the artifact into a `scratch` image. This reduces distribution size and attack surface, and demonstrates the typical pattern to containerize compiled-language applications efficiently.
