# Lab 2 Bonus — Multi-Stage Docker Build for Go Application

## Multi-Stage Strategy

### Stage 1: Builder
```dockerfile
# Stage 1: Builder - full build environment
FROM golang:1.21-alpine AS builder

# Install system dependencies for build (git for go mod download)
RUN apk add --no-cache git ca-certificates

# Set working directory
WORKDIR /app

# Copy Go module files
COPY go.mod ./

# Download Go module dependencies
RUN go mod download

# Copy application source code
COPY . .

# Build Go application with optimizations
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -a \
    -ldflags="-w -s -extldflags '-static'" \
    -o devops-info-service .
```

**Purpose:** Complete build environment containing:
- Go 1.21 compiler and standard library
- Git for dependency management
- All source code and build tools
- Temporary workspace for compilation

### Stage 2: Runtime
```dockerfile
FROM scratch

# Copy CA certificates from builder for HTTPS support
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

# Copy the compiled binary from builder
COPY --from=builder /app/devops-info-service /app/devops-info-service

# Expose port
EXPOSE 5000

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=5000

# Run the application
CMD ["/app/devops-info-service"]
```

**Purpose:** Absolute minimal runtime environment containing only:
- Statically compiled Go binary
- CA certificates for HTTPS/TLS support
- No operating system, shell, or package manager

## Size Comparison

### Image Size Analysis
| Component | Size | Contents |
|-----------|------|----------|
| **Builder Stage** | ~350MB | Full Go 1.21 SDK + Alpine + build tools |
| **Runtime Stage** | **7.16MB** | Static binary + CA certificates |
| **Size Reduction** | **~98%** | 350MB → 7.16MB |

### Detailed Breakdown
- **Builder image:** Uses `golang:1.21-alpine` (~350MB with build tools)
- **Final image:** Uses `scratch` (0MB base) + binary + certificates
- **Binary size:** ~7.16MB (statically compiled Go application + CA certificate)

## Why Multi-Stage Builds Matter for Compiled Languages

### 1. Drastic Size Reduction
Compiled languages like Go have a fundamental advantage: they produce standalone binaries. Multi-stage builds leverage this by:
- **Separating concerns:** Build environment (large) vs runtime (minimal)
- **Eliminating build tools:** Compiler, linker, SDK removed from production
- **Removing dependencies:** Only the binary and absolute essentials remain

### 2. Enhanced Security
```dockerfile
FROM scratch  # No operating system, no shell, no package manager
```

**Security benefits:**
- **No shell access:** Cannot spawn shells even if compromised
- **Immutable runtime:** Binary cannot be modified without rebuilding
- **Principle of least privilege:** Only what's absolutely necessary

### 3. Production Performance
- **Faster deployment:** Smaller images download quicker 
- **Reduced storage:** Less disk space required across development/staging/production
- **Lower memory footprint:** Minimal OS overhead
- **Quick startup:** No initialization of unused services

## Terminal Output

### Build Process Output
```bash
s3rap1s in ~/devops/DevOps-Core-Course/app_go on lab01 ● ● λ docker build -t devops-info-service:go .
[+] Building 5.1s (14/14) FINISHED                                                                                                                        docker:default
 => [internal] load build definition from Dockerfile                                                                                                                0.0s
 => => transferring dockerfile: 1.00kB                                                                                                                              0.0s
 => [internal] load metadata for docker.io/library/golang:1.21-alpine                                                                                               0.7s
 => [internal] load .dockerignore                                                                                                                                   0.0s
 => => transferring context: 359B                                                                                                                                   0.0s
 => [builder 1/7] FROM docker.io/library/golang:1.21-alpine@sha256:2414035b086e3c42b99654c8b26e6f5b1b1598080d65fd03c7f499552ff4dc94                                 0.0s
 => => resolve docker.io/library/golang:1.21-alpine@sha256:2414035b086e3c42b99654c8b26e6f5b1b1598080d65fd03c7f499552ff4dc94                                         0.0s
 => [internal] load build context                                                                                                                                   0.0s
 => => transferring context: 54B                                                                                                                                    0.0s
 => CACHED [builder 2/7] RUN apk add --no-cache git ca-certificates                                                                                                 0.0s
 => CACHED [builder 3/7] WORKDIR /app                                                                                                                               0.0s
 => CACHED [builder 4/7] COPY go.mod ./                                                                                                                             0.0s
 => CACHED [builder 5/7] RUN go mod download                                                                                                                        0.0s
 => CACHED [builder 6/7] COPY . .                                                                                                                                   0.0s
 => [builder 7/7] RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build     -a     -ldflags="-w -s -extldflags '-static'"     -o devops-info-service .                 3.9s
 => [stage-1 1/2] COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/                                                                            0.0s
 => [stage-1 2/2] COPY --from=builder /app/devops-info-service /app/devops-info-service                                                                             0.0s
 => exporting to image                                                                                                                                              0.4s
 => => exporting layers                                                                                                                                             0.3s
 => => exporting manifest sha256:4e1764a6a80bfc8666f97655b398a31766e6ef0b7e113b73651ca44601a369e5                                                                   0.0s
 => => exporting config sha256:07f16274913e502fcb7339751611566f733555d340310768666604f24375006b                                                                     0.0s
 => => exporting attestation manifest sha256:594b42605a1d485598b5ca39be853c1e154958e927a235027e0ca1b5fce2efa9                                                       0.0s
 => => exporting manifest list sha256:c5f945015fb0dfd3f762151c64c5393121944441d08e191e5a7533aadcf4f4eb                                                              0.0s
 => => naming to docker.io/library/devops-info-service:go                                                                                                           0.0s
 => => unpacking to docker.io/library/devops-info-service:go     
```

### Image Size Verification
```bash
s3rap1s in ~/devops/DevOps-Core-Course/app_go on lab01 ● ● λ docker images | grep devops-info-service
WARNING: This output is designed for human readability. For machine-readable output, please use --format.
devops-info-service:go                                          c5f945015fb0       7.16MB          2.2MB   U    
devops-info-service:python                                      4b08b6e2f063        199MB         48.1MB        
s3rap1s/devops-info-service:python                              ef074c1a118d        199MB         48.1MB  

s3rap1s in ~/devops/DevOps-Core-Course/app_go on lab01 ● ● λ docker history devops-info-service:go
IMAGE          CREATED          CREATED BY                                      SIZE      COMMENT
c5f945015fb0   14 minutes ago   CMD ["/app/devops-info-service"]                0B        buildkit.dockerfile.v0
<missing>      14 minutes ago   ENV PORT=5000                                   0B        buildkit.dockerfile.v0
<missing>      14 minutes ago   ENV HOST=0.0.0.0                                0B        buildkit.dockerfile.v0
<missing>      14 minutes ago   EXPOSE [5000/tcp]                               0B        buildkit.dockerfile.v0
<missing>      14 minutes ago   COPY /app/devops-info-service /app/devops-in…   4.72MB    buildkit.dockerfile.v0
<missing>      14 minutes ago   COPY /etc/ssl/certs/ca-certificates.crt /etc…   238kB     buildkit.dockerfile.v0
```

### Runtime Testing
```bash
s3rap1s in ~/devops/DevOps-Core-Course/app_go on lab01 ● ● λ docker run -d --name devops-go -p 5000:5000 devops-info-service:go
0d2cb36ff83b03fca8090248aa3a6fe1beba1e879617a8dd2e5a9c3a588e8c1c

s3rap1s in ~/devops/DevOps-Core-Course/app_go on lab01 ● ● λ curl http://localhost:5000/      
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"Go"},"system":{"hostname":"0d2cb36ff83b","platform":"linux","platform_version":"Linux Kernel","architecture":"amd64","cpu_count":12,"go_version":"go1.21.13"},"runtime":{"uptime_seconds":17,"uptime_human":"0 hours, 0 minutes","current_time":"2026-01-31T20:20:36Z","timezone":"UTC"},"request":{"client_ip":"172.17.0.1:50750","user_agent":"curl/8.18.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"}]}

s3rap1s in ~/devops/DevOps-Core-Course/app_go on lab01 ● ● λ curl http://localhost:5000/health
{"status":"healthy","timestamp":"2026-01-31T20:21:20Z","uptime_seconds":61}

s3rap1s in ~/devops/DevOps-Core-Course/app_go on lab01 ● ● λ docker logs devops-go
2026/01/31 20:20:19 Starting DevOps Info Service on 0.0.0.0:5000
2026/01/31 20:20:34 Health check from 172.17.0.1:50742
2026/01/31 20:20:36 Request: GET / from 172.17.0.1:50750
2026/01/31 20:21:13 404 Not Found: /helath
2026/01/31 20:21:20 Health check from 172.17.0.1:38286
```

## Technical Explanation of Each Stage

### Stage 1: Builder (`golang:1.21-alpine`)
**Purpose:** Provide complete compilation environment

**Key operations:**
1. **Base setup:** Alpine Linux with Go 1.21 toolchain
2. **Dependencies:** Install git and CA certificates
3. **Module management:** Download Go dependencies with caching
4. **Compilation:** Build optimized static binary with:
   - `CGO_ENABLED=0`: Disable CGO for pure Go static binary
   - `-ldflags="-w -s"`: Strip debug symbols and DWARF tables
   - `-extldflags '-static'`: Force static linking
   - `-a`: Force rebuilding of packages

**Output:** `/app/devops-info-service` (6.9MB static binary)

### Stage 2: Runtime (`scratch`)
**Purpose:** Provide minimal production runtime

**Key operations:**
1. **Base image:** `scratch` (empty filesystem)
2. **Binary copy:** Transfer compiled binary from builder
3. **Certificates:** Copy CA certificates for TLS/HTTPS support
4. **Configuration:** Set environment variables and expose port

**Output:** Production-ready container image (7.16MB)

## Security Benefits of Smaller Images

### Specific Security Advantages
1. **No shell:** Cannot execute arbitrary commands or spawn shells
2. **Immutable filesystem:** Only the binary exists, cannot be modified
3. **Minimal CVE surface:** No packages = no vulnerabilities to patch
4. **Isolated execution:** Runs as PID 1 with no background services
5. **Resource limits:** Minimal memory/cpu usage reduces DoS impact

## Why FROM scratch? Trade-offs and Decisions

### Why `scratch` Was Chosen
```dockerfile
FROM scratch  # Instead of alpine, distroless, or other minimal bases
```

**Advantages:**
1. **Absolute minimalism:** 0MB base, only binary + certs
2. **Maximum security:** No OS, no shell, no utilities
3. **Great for static binaries:** Go compiles to fully static executables

### Trade-offs Considered
| Base Image | Size | Pros | Cons | Decision |
|------------|------|------|------|----------|
| **scratch** | 0MB | Max security, minimal size | No debugging tools, no shell | ✅ **Chosen** |
| **alpine** | 5.5MB | Shell for debugging, small | Larger, more attack surface | Rejected |
| **distroless** | 20MB | Secure | Much larger than scratch | Rejected |

## Analysis of Size Reduction and Why It Matters

### Why Size Reduction Matters
1. **Cost efficiency:** 98% reduction in storage and bandwidth costs
2. **Deployment speed:** Images deploy in seconds instead of minutes
3. **Developer productivity:** Faster CI/CD pipeline execution
4. **Environmental impact:** Less energy for storage and transfer
5. **Edge computing:** Suitable for resource-constrained environments

## Challenges and Solutions

### Challenge: Certificate Management with `scratch`
**Problem:** `scratch` has no CA certificates, breaking HTTPS calls from the application.

**Solution:** Copy certificates from builder stage:
```dockerfile
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
```

## What I Learned

1. **Multi-stage builds** are transformative for compiled languages, enabling near-zero runtime overhead
2. **Static compilation** is powerful but requires careful dependency management
3. **Security through minimalism** is achievable with `scratch` base images
4. **Trade-offs exist** between debuggability and security/minimalism
