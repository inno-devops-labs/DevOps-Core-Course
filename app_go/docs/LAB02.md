# Multi-stage build strategy
## Stage 1 - Builder
**Purpose:** compile the Go application using a full Go toolchain image.

**Key points:**
- Uses `golang:1.22-alpine` to keep the builder stage smaller than Debian-based images.
- Copies `go.mod` first and runs `go mod download` to maximize Docker layer caching.
- Builds a Linux binary with `CGO_ENABLED=0` (static binary), which allows a minimal runtime image.

**Dockerfile snippet:**
```dockerfile
FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY go.mod ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o myapp
```

## Stage 2 - Runtime
**Purpose:** run only the compiled binary in a minimal image with a non-root user.

**Key points:**
- Uses `gcr.io/distroless/static-debian12:nonroot`.
- Distroless images contain only what is required to run the app (no package manager, no shell), reducing image size and attack surface.
- Runs as a **non-root** user (provided by the `:nonroot` tag).

**Dockerfile snippet:**
```dockerfile
FROM gcr.io/distroless/static-debian12:nonroot
WORKDIR /app
COPY --from=builder /app/myapp .
EXPOSE 8080
CMD ["./myapp"]
```

# Size comparison with analysis (builder vs final image)
## Builder
```bash
docker images newspec/app_go:builder
REPOSITORY       TAG       IMAGE ID       CREATED          SIZE
newspec/app_go   builder   21b01f8c6103   37 minutes ago   305MB
```
## Final
```bash
docker images newspec/app_go:1.0
REPOSITORY       TAG       IMAGE ID       CREATED          SIZE  
newspec/app_go   1.0       a944205e6030   59 minutes ago   9.32MB
```
## Analysis
The builder image contains the Go toolchain and build dependencies, so it is significantly larger.
The final image contains only the static binary, which is much smaller and safer.

# Why multi-stage builds matter for compiled languages

Compiled languages (like Go, Rust, Java with native images, etc.) typically require a **heavy build environment**: compilers, linkers, SDKs, package managers, and temporary build artifacts. If you ship that same environment as your runtime container, the final image becomes unnecessarily large and less secure.

Multi-stage builds solve this by separating concerns:

### 1) Smaller final images (faster pull & deploy)
- The **builder stage** includes the full toolchain (large).
- The **runtime stage** contains only the compiled output (usually just a single binary).
This dramatically reduces image size, which improves:
- CI/CD speed (less time to push/pull)
- Startup speed (faster distribution in clusters)
- Bandwidth/storage usage

### 2) Better security (smaller attack surface)
The runtime image no longer contains:
- compilers (go, gcc, build tools)
- package managers
- shells and utilities (especially with distroless/scratch)

Fewer components, so fewer potential vulnerabilities (CVEs) and fewer tools available to an attacker if the container is compromised.

### 3) Cleaner separation of build vs runtime
Multi-stage builds enforce a clear boundary:
- build dependencies exist only where needed (builder stage)
- runtime image stays minimal and focused on execution

This makes the container easier to reason about and maintain.

### 4) Reproducible and cache-friendly builds
When the Dockerfile copies dependency descriptors first (e.g., `go.mod`/`go.sum`) and downloads dependencies before copying source code:
- Docker can reuse cached layers if dependencies are unchanged
- rebuilds after code changes are significantly faster

### 5) Enables ultra-minimal runtime images
Compiled apps can often run in very small base images:
- `distroless` (secure and minimal)
- `scratch` (almost empty)

This is usually impossible for interpreted languages without bundling an interpreter runtime.

**Summary:** For compiled languages, multi-stage builds provide the best of both worlds — a full build environment when you need it, and a minimal secure runtime image when you deploy.

# Terminal output showing build process
## Builder
```bash
docker build --target builder -t newspec/app_go:builder .
[+] Building 2.4s (12/12) FINISHED                                                                                                                                                   docker:desktop-linux
 => [internal] load build definition from Dockerfile                                                                                                                                                 0.0s
 => => transferring dockerfile: 349B                                                                                                                                                                 0.0s
 => [internal] load metadata for docker.io/library/golang:1.22-alpine                                                                                                                                2.1s
 => [auth] library/golang:pull token for registry-1.docker.io                                                                                                                                        0.0s
 => [internal] load .dockerignore                                                                                                                                                                    0.1s
 => => transferring context: 105B                                                                                                                                                                    0.0s
 => [builder 1/6] FROM docker.io/library/golang:1.22-alpine@sha256:1699c10032ca2582ec89a24a1312d986a3f094aed3d5c1147b19880afe40e052                                                                  0.0s
 => [internal] load build context                                                                                                                                                                    0.0s
 => => transferring context: 146B                                                                                                                                                                    0.0s
 => CACHED [builder 2/6] WORKDIR /app                                                                                                                                                                0.0s
 => CACHED [builder 3/6] COPY go.mod ./                                                                                                                                                              0.0s 
 => CACHED [builder 4/6] RUN go mod download                                                                                                                                                         0.0s 
 => CACHED [builder 5/6] COPY . .                                                                                                                                                                    0.0s 
 => CACHED [builder 6/6] RUN CGO_ENABLED=0 go build -o myapp                                                                                                                                         0.0s 
 => exporting to image                                                                                                                                                                               0.0s 
 => => exporting layers                                                                                                                                                                              0.0s 
 => => writing image sha256:21b01f8c61038149b9130afe7881765d625b2eb6622b6b46f42682d26b10ae2b                                                                                                         0.0s 
 => => naming to docker.io/newspec/app_go:builder                                                                                                                                                    0.0s 

View build details: docker-desktop://dashboard/build/desktop-linux/desktop-linux/wvw3g1yzoqu1uput2mz8me7zx
```

## Final
```bash
docker build -t newspec/app_go:1.0 .
[+] Building 1.5s (15/15) FINISHED                                                                                                                                                   docker:desktop-linux
 => [internal] load build definition from Dockerfile                                                                                                                                                 0.0s
 => => transferring dockerfile: 349B                                                                                                                                                                 0.0s 
 => [internal] load metadata for gcr.io/distroless/static-debian12:nonroot                                                                                                                           1.0s 
 => [internal] load metadata for docker.io/library/golang:1.22-alpine                                                                                                                                0.7s 
 => [internal] load .dockerignore                                                                                                                                                                    0.0s
 => => transferring context: 105B                                                                                                                                                                    0.0s 
 => [builder 1/6] FROM docker.io/library/golang:1.22-alpine@sha256:1699c10032ca2582ec89a24a1312d986a3f094aed3d5c1147b19880afe40e052                                                                  0.0s 
 => [stage-1 1/3] FROM gcr.io/distroless/static-debian12:nonroot@sha256:cba10d7abd3e203428e86f5b2d7fd5eb7d8987c387864ae4996cf97191b33764                                                             0.0s 
 => [internal] load build context                                                                                                                                                                    0.0s 
 => => transferring context: 146B                                                                                                                                                                    0.0s 
 => CACHED [builder 2/6] WORKDIR /app                                                                                                                                                                0.0s 
 => CACHED [builder 3/6] COPY go.mod ./                                                                                                                                                              0.0s 
 => CACHED [builder 4/6] RUN go mod download                                                                                                                                                         0.0s 
 => CACHED [builder 5/6] COPY . .                                                                                                                                                                    0.0s 
 => CACHED [builder 6/6] RUN CGO_ENABLED=0 go build -o myapp                                                                                                                                         0.0s 
 => CACHED [stage-1 2/3] WORKDIR /app                                                                                                                                                                0.0s
 => CACHED [stage-1 3/3] COPY --from=builder /app/myapp .                                                                                                                                            0.0s 
 => exporting to image                                                                                                                                                                               0.1s 
 => => exporting layers                                                                                                                                                                              0.0s 
 => => writing image sha256:c9ff1572d8a13240f00ef7d66683264e0fbf4fa77c12790dc3f3428972819321                                                                                                         0.0s 
 => => naming to docker.io/newspec/app_go:1.0                                                                                                                                                        0.0s 

View build details: docker-desktop://dashboard/build/desktop-linux/desktop-linux/nvdyhylzo1hzpemy23lt42ll1
```
# Technical explanation of each stage's purpose
### Stage 1 — Builder (Compile Environment)
**Goal:** Produce a Linux executable from Go source code in a controlled build environment.

**Why this stage exists:**
- Go compilation requires the Go toolchain (compiler, linker) which is large and should not be shipped in the final runtime image.
- The builder image provides everything needed to compile the application.

**What happens technically:**
1. **Set working directory**
   - `WORKDIR /app` defines where source code and build steps run inside the container.

2. **Copy dependency definition first**
   - `COPY go.mod ./` is done before copying the whole source tree.
   - This allows Docker to cache the dependency download layer.
   - Even if code changes, dependencies may not, so rebuilds are faster.

3. **Download modules**
   - `RUN go mod download` fetches required modules.
   - In this project there are no external module dependencies, so Go prints:
     `go: no module dependencies to download`
   - The step is still good practice and keeps the Dockerfile consistent for future changes.

4. **Copy application source code**
   - `COPY . .` brings in the Go source files.
   - This layer changes most often, so it comes after dependency caching steps.

5. **Compile a static binary**
   - `RUN CGO_ENABLED=0 go build -o myapp`
   - `CGO_ENABLED=0` disables C bindings so the binary is statically linked.
   - A static binary does not require libc or other runtime shared libraries, enabling minimal runtime images.

**Output of the stage:** a compiled executable (`/app/myapp`).

---

### Stage 2 — Runtime (Execution Environment)
**Goal:** Run only the compiled binary in a minimal and secure container image.

**Why this stage exists:**
- The runtime stage should not contain compilers, source code, or build tools.
- A smaller runtime image reduces attack surface and improves deployment speed.

**What happens technically:**
1. **Choose a minimal base image**
   - `FROM gcr.io/distroless/static-debian12:nonroot`
   - Distroless images contain only the minimum required runtime files.
   - The `:nonroot` variant runs as a non-root user by default.

2. **Set working directory**
   - `WORKDIR /app` provides a predictable location for the binary.

3. **Copy only the build artifact**
   - `COPY --from=builder /app/myapp .`
   - This copies only the compiled binary from the builder stage.
   - No source code, no Go toolchain, no dependency caches are included.

4. **Run the application**
   - `CMD ["./myapp"]` starts the service.
   - The application reads `HOST` and `PORT` environment variables:
     - defaults: `HOST=0.0.0.0`, `PORT=8080`
   - When running the container, port mapping must match the internal listening port (e.g., `-p 8000:8080`).

**Output of the stage:** a minimal runtime container that executes the Go binary as a non-root user.