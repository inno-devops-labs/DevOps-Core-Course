# DevOps Info Service - Go Multi-Stage Build
# Produces a minimal container with only the compiled binary

# ============================================
# Stage 1: Builder
# ============================================
# Use official Go image for compilation
FROM golang:1.21-alpine AS builder

# Set working directory
WORKDIR /build

# Copy go module files first (dependency caching)
COPY go.mod ./

# Download dependencies (cached if go.mod unchanged)
RUN go mod download

# Copy source code
COPY main.go ./

# Build static binary
# CGO_ENABLED=0: Create static binary (no C dependencies)
# -ldflags="-s -w": Strip debug info to reduce binary size
# -o: Output file name
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -ldflags="-s -w" \
    -o devops-info-service main.go

# ============================================
# Stage 2: Runtime
# ============================================
# Use scratch (empty) image for minimal size
# Alternative: alpine (~5MB) if you need shell access
FROM scratch

# Copy CA certificates for HTTPS (if needed in future)
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

# Copy the binary from builder stage
COPY --from=builder /build/devops-info-service /devops-info-service

# Document the port
EXPOSE 8080

# Run the binary
# Note: scratch images have no shell, so we use exec form
ENTRYPOINT ["/devops-info-service"]
