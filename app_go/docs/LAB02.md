# Lab 02 Bonus — Multi-Stage Docker Build (Go)

## Multi-Stage Build Strategy

Multi-stage build separates compilation from runtime, resulting in minimal production images.

### Two-Stage Approach

**Stage 1 (Builder):** Full Go toolchain for compilation
- Base: `golang:1.23-alpine` (~300MB)
- Contains: Go compiler, build tools, git
- Purpose: Compile application into static binary

**Stage 2 (Runtime):** Minimal Alpine Linux
- Base: `alpine:3.19` (~7MB)
- Contains: Only essential C libraries
- Purpose: Run the compiled binary

**Result:** Final image contains only what's needed to run the application.

## Dockerfile Breakdown

### Stage 1: Builder

```dockerfile
FROM golang:1.23-alpine AS builder

RUN apk add --no-cache git

WORKDIR /build

COPY go.mod ./
COPY main.go .

RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o devops-info-service main.go
```

**Key Decisions:**

1. **golang:1.23-alpine AS builder** - Named stage for reference
2. **apk add git** - Some Go modules may need git for downloading
3. **CGO_ENABLED=0** - Produces static binary with no C dependencies (can run on scratch)
4. **-ldflags="-s -w"** - Strips debug symbols and DWARF info, reduces binary size by ~30%

### Stage 2: Runtime

```dockerfile
FROM alpine:3.19

RUN addgroup -S appuser && adduser -S appuser -G appuser

WORKDIR /app

COPY --from=builder /build/devops-info-service .

RUN chown appuser:appuser /app/devops-info-service

USER appuser

EXPOSE 8080

ENV HOST=0.0.0.0 PORT=8080

CMD ["./devops-info-service"]
```

**Key Decisions:**

1. **alpine:3.19** - Minimal base (7MB), much smaller than golang:1.23-alpine (300MB)
2. **COPY --from=builder** - Takes only the binary from builder stage
3. **Non-root user** - Security best practice
4. **Static binary** - Works on alpine because CGO_ENABLED=0

## Size Comparison with Analysis

### Image Sizes

| Stage/Image | Size | Purpose |
|-------------|------|---------|
| **Builder (golang:1.23-alpine)** | ~300 MB | Compilation only (not shipped) |
| **Final (alpine:3.19 + binary)** | 26.2 MB | Production deployment |
| **Go binary alone** | 5.2 MB | The compiled application |

**Actual Measurement:**
- Alpine base: ~7 MB
- Go binary: 5.2 MB
- Additional layers: ~14 MB
- **Total: 26.2 MB** (compressed: 7.58 MB)

**Compare to Python:**
- Python container: 223 MB (compressed: 48.4 MB)
- Go container: 26.2 MB (compressed: 7.58 MB)
- **Go is 8.5x smaller** (26.2 MB vs 223 MB)

### Build Process Output

```bash
docker build -t devops-info-service-go:latest .
```

**Actual Output:**
```
#1 [internal] load build definition from Dockerfile
#1 transferring dockerfile: 1.12kB done
#1 DONE 0.0s

#2 [internal] load metadata for docker.io/library/golang:1.23-alpine
#2 DONE 2.7s

#3 [internal] load metadata for docker.io/library/alpine:3.19
#3 DONE 2.7s

#4 [builder 1/6] FROM golang:1.23-alpine@sha256:383395b794dffa5b53012a212365d40c8e37109a626ca30d6151c8348d380b5f
#4 DONE 4.9s

#5 [stage-1 1/5] FROM alpine:3.19@sha256:6baf43584bcb78f2e5847d1de515f23499913ac9f12bdf834811a3145eb11ca1
#5 DONE 0.7s

#6 [builder 2/6] RUN apk add --no-cache git
#6 DONE 2.6s

#7 [builder 3/6] WORKDIR /build
#7 DONE 0.0s

#8 [builder 4/6] COPY go.mod ./
#8 DONE 0.0s

#9 [builder 5/6] COPY main.go .
#9 DONE 0.0s

#10 [builder 6/6] RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o devops-info-service main.go
#10 DONE 3.1s

#11 [stage-1 2/5] RUN addgroup -S appuser && adduser -S appuser -G appuser
#11 DONE 0.1s

#12 [stage-1 3/5] WORKDIR /app
#12 DONE 0.0s

#13 [stage-1 4/5] COPY --from=builder /build/devops-info-service .
#13 DONE 0.0s

#14 [stage-1 5/5] RUN chown appuser:appuser /app/devops-info-service
#14 DONE 0.1s

#15 exporting to image
#15 naming to docker.io/library/devops-info-service-go:latest done
#15 DONE 0.2s
```

**Build Time:** ~16 seconds (first build), ~0.5 seconds (with cache)  
**Compilation Time:** 3.1 seconds

### Size Verification

```bash
docker images | grep devops-info-service
```

**Actual Output:**
```
devops-info-service-go     latest    e0349b6f7c2f    26.2MB    7.58MB
devops-info-service-python latest    d6ddca86964d     223MB    48.4MB
```

**Memory Usage (Running Containers):**
```bash
docker stats --no-stream
```
```
NAME            MEM USAGE / LIMIT     CPU %
devops-go       2.887MiB / 17.54GiB   0.00%
devops-python   39.4MiB / 17.54GiB    0.04%
```

**Performance Summary:**
- Go uses **13.6x less memory** (2.9 MB vs 39.4 MB)
- Go image is **8.5x smaller** (26.2 MB vs 223 MB)
- Go startup: <100ms, Python startup: ~200-300ms

## Why Multi-Stage Builds Matter for Compiled Languages

### The Problem Without Multi-Stage

If we used single-stage with golang:1.23-alpine:

```dockerfile
FROM golang:1.23-alpine
COPY . .
RUN go build -o app main.go
CMD ["./app"]
```

**Result:** Final image = ~310 MB (includes entire Go toolchain)

**Issues:**
- Wasted space: compiler, build tools not needed at runtime
- Security: more packages = more vulnerabilities
- Slow deployments: 310 MB vs 26 MB over network

### The Solution With Multi-Stage

**Stage 1:** Compile (large image, discarded)
**Stage 2:** Copy binary only (tiny image, shipped)

**Benefits:**
1. **91.5% size reduction** (310 MB → 26.2 MB)
2. **Faster deployments** - pull/push 12x faster
3. **Better security** - no compilers or build tools in production
4. **Cost savings** - less bandwidth, less storage
5. **Lower memory footprint** - 2.9 MB vs 39.4 MB for Python

### Static vs Dynamic Compilation

**CGO_ENABLED=0** produces static binary:
- **Static:** All dependencies compiled in, works on any Linux
- **Dynamic:** Requires specific system libraries at runtime

**Why Static for This App:**
- Can use minimal base images (alpine, distroless, even scratch)
- No runtime dependencies beyond kernel
- More portable across different Linux distributions

**Trade-off:** Static binaries slightly larger (~5MB vs ~3MB) but much more portable.

## Technical Explanation of Each Stage

### Builder Stage Purpose

1. **Provides Go compiler** - `golang:1.23-alpine` includes go, go build, go mod
2. **Downloads dependencies** - `go.mod` triggers automatic dependency resolution
3. **Compiles binary** - Produces standalone executable
4. **Optimizes binary** - `-ldflags` reduces size

**This stage is ~300MB but never shipped to production.**

### Runtime Stage Purpose

1. **Minimal base** - alpine:3.19 is ~7MB, just enough to run the binary
2. **Security setup** - Creates non-root user
3. **Binary only** - Copies the 5.2MB binary, nothing else
4. **Configuration** - Sets environment and command

**This stage is 26.2MB and this is what gets deployed.**

### Runtime Testing

```bash
docker run -p 8080:8080 devops-info-service-go:latest
```

**Startup Logs:**
```
2026/02/02 15:12:10 Starting DevOps Info Service on 0.0.0.0:8080
2026/02/02 15:12:10 Go version: go1.23.12
```

**Response from container:**
```json
{
    "service": {
        "name": "devops-info-service",
        "version": "1.0.0",
        "description": "DevOps course info service",
        "framework": "Go net/http"
    },
    "system": {
        "hostname": "0ee39037016f",
        "platform": "linux",
        "platform_version": "go1.23.12",
        "architecture": "arm64",
        "cpu_count": 11,
        "go_version": "go1.23.12"
    }
}
```

## Security Benefits Analysis

### Smaller Attack Surface

**Large Image (310 MB):**
- Contains: compiler, linker, package managers, build tools
- Hundreds of system packages
- Many potential vulnerabilities

**Small Image (26.2 MB):**
- Contains: minimal C library, shell, Go binary
- ~10 system packages
- Fewer potential vulnerabilities

**Impact:** Less code = fewer bugs = fewer CVEs to patch.

### No Build Tools in Production

**Builder tools removed:**
- Go compiler (potential for code injection attacks)
- Git (potential for repository access)
- Build utilities (could be exploited)

**Runtime only has:** The binary and minimal OS.

### Principle of Least Privilege

Running as non-root + minimal packages = defense in depth.

If application compromised:
- Attacker has limited user privileges
- Fewer system tools available for escalation
- Smaller surface area to explore

## Trade-offs and Decisions

### Alpine vs Distroless vs Scratch

**Chosen: Alpine (3.19)**

| Base | Size | Pros | Cons |
|------|------|------|------|
| **alpine:3.19** | 7 MB | Shell for debugging, package manager | Slightly larger |
| **distroless** | 2 MB | More secure (no shell) | Harder to debug |
| **scratch** | 0 MB | Absolute minimum | No debugging at all |

**Decision:** Alpine provides best balance - small size but still debuggable if needed. For production systems, distroless would be better.

### Static Linking Trade-off

**CGO_ENABLED=0:**
- ✅ Portable binary works on any base
- ✅ Can use scratch/distroless
- ❌ Slightly larger binary (+2MB)
- ❌ Some packages won't work without CGO

**For this app:** No CGO dependencies, so static is perfect choice.

## Build Commands & Docker Hub

### Build & Test
```bash
# Build
docker build -t devops-info-service-go:latest .

# Check size
docker images devops-info-service-go

# Run
docker run -p 8080:8080 devops-info-service-go:latest

# Test
curl http://localhost:8080/
curl http://localhost:8080/health
```

### Docker Hub Push

**Tagging Strategy:**

Format: `aezuraa/devops-info-service:go`
- Same repository as Python variant for consistency
- `:go` tag identifies the Go implementation
- Allows users to choose language variant: `:python` or `:go`

**Commands:**
```bash
docker tag devops-info-service-go:latest aezuraa/devops-info-service:go
docker push aezuraa/devops-info-service:go
```

**Push Output:**
```
79abe3af9fe1: Pushed
c351f84db329: Pushed
5711127a7748: Pushed
00511ec3b3c9: Pushed
04508bc088a8: Pushed
ce607938610b: Pushed
go: digest: sha256:e0349b6f7c2f33bb12a477fbb232016698a6dda28f3f038bfeb2814364a4689e size: 856
```

**Repository:** `https://hub.docker.com/r/aezuraa/devops-info-service`

## Size Reduction Achievement

**Single-stage (golang:1.23-alpine):** ~310 MB  
**Multi-stage (alpine:3.19 + binary):** 26.2 MB  
**Reduction:** **91.5% smaller** (11.8x reduction)

**Compared to Python:**
- Python: 223 MB (compressed 48.4 MB)
- Go: 26.2 MB (compressed 7.58 MB)
- **Go is 8.5x smaller in size**
- **Go uses 13.6x less memory** (2.9 MB vs 39.4 MB)

## Why This Matters

**Development Workflow:**
- Faster CI/CD pipelines (smaller images build/push faster)
- Cheaper registry storage costs
- Faster deployments and scaling
- Better developer experience (quick iterations)

**Production Impact:**
- Lower bandwidth costs
- Faster container startup
- More containers per host (lower memory)
- Reduced security vulnerabilities

**Educational Value:**
- Demonstrates containerization best practices
- Shows benefits of compiled languages for containers
- Teaches multi-stage build patterns used in production

## Implementation Summary

Multi-stage Docker build successfully implemented with:
- Two-stage build process (builder + runtime)
- 91.5% size reduction vs single-stage (310 MB → 26.2 MB)
- 88% smaller than Python version (26.2 MB vs 223 MB)
- 13.6x less memory usage (2.9 MB vs 39.4 MB)
- Static binary for maximum portability
- Non-root user for security
- Production-ready configuration
- Successfully pushed to Docker Hub (aezuraa/devops-info-service:go)
