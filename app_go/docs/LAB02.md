# Lab 2 — Multi-Stage Build (Go App)

## 1. Multi-Stage Build Strategy

- **Stage 1 — Builder**
  - **Base image**: `golang:1.21-alpine`.
  - **Purpose**: Provide the full Go toolchain and a lightweight Alpine-based environment to compile the application.
  - **Key steps**:
    - Set the working directory to `/src`.
    - Copy `go.mod` and download dependencies to leverage layer caching.
    - Copy the rest of the source code and run `go build` to produce a static binary.
  - **Snippet**:
    ```dockerfile
    FROM golang:1.21-alpine AS builder
    WORKDIR /src
    COPY go.mod .
    RUN go mod download
    COPY . .
    RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o /bin/devops-info-service main.go
    ```

- **Stage 2 — Runtime**
  - **Base image**: `gcr.io/distroless/base-debian12`.
  - **Purpose**: Provide a minimal, secure runtime environment with almost no extra tools installed.
  - **Key steps**:
    - Set working directory to `/app`.
    - Copy only the compiled binary from the builder stage.
    - Configure environment variables and expose the HTTP port.
    - Run as a non-root user provided by the distroless image.
  - **Snippet**:
    ```dockerfile
    FROM gcr.io/distroless/base-debian12 AS runtime
    WORKDIR /app
    COPY --from=builder /bin/devops-info-service /app/devops-info-service
    EXPOSE 8080
    ENV HOST=0.0.0.0 PORT=8080
    USER nonroot:nonroot
    ENTRYPOINT ["/app/devops-info-service"]
    ```

## 2. Image Size Comparison

![alt](/app_go/docs/screenshots/go-vs-python-docker.jpg)

- **Builder image (golang:1.21-alpine based)**
  - Contains: Go compiler, build tools, module cache, and full source tree.

- **Final runtime image (distroless)**
  - Contains: Only the compiled binary plus a minimal runtime base.

- **Analysis**
  - Why it matters: Smaller images are faster to pull and start, reduce bandwidth and storage usage, and have a smaller attack surface because they include fewer utilities and libraries.

## 3. Build & Run Process

### 3.1 Build Images

```text
# docker build -t go-app .
```
![alt](/app_go/docs/screenshots/go-build-docker.jpg)

### 3.2 Run Container

```text
# docker run --rm -p 8080:8080 go-app
```
![alt](/app_go/docs/screenshots/go-start-docker.jpg)

### 3.3 Image Sizes

## 4. Why Multi-Stage Builds Matter

- **Smaller final images**
  - Builder images include compilers, headers, and build tools that are unnecessary at runtime.
  - By copying only the compiled binary into the final stage, the runtime image shrinks dramatically.

- **Security benefits**
  - Fewer tools (no shell, package manager, compiler) means fewer potential escalation paths for an attacker.
  - Distroless images are designed with security in mind: they contain just enough to run the application.

- **Clear separation of concerns**
  - Build logic (dependencies, compilation) lives in the builder stage.
  - Runtime stage focuses only on running the compiled artifact.

- **Performance and operational impact**
  - Faster pulls and deploys, especially in clustered environments like Kubernetes.
  - Less storage used in registries and on nodes.

## 5. Technical Explanation of Each Stage

- **Builder stage**
  - Uses Go modules from `go.mod` to fetch dependencies.
  - `CGO_ENABLED=0` ensures a statically linked binary, making it easier to run in a minimal base image that might not have system libraries.
  - Targets `linux/amd64` so the binary runs on common container runtimes.

- **Runtime stage**
  - Distroless base provides the minimal libraries needed by the binary and a non-root user by default.
  - `EXPOSE 8080` documents the application port; combined with `ENV HOST`/`PORT`, it mirrors the same configuration pattern as the non-containerized app.
  - `ENTRYPOINT` runs the binary directly without an extra shell process.


