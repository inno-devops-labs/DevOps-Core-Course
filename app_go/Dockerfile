# DevOps Info Service - Go Multi-Stage Dockerfile
# Demonstrates efficient containerization of compiled languages

# =============================================================================
# Stage 1: Builder - Compile the Go application
# =============================================================================
FROM golang:1.21-alpine AS builder

ARG TARGETOS=linux
ARG TARGETARCH

# Install CA certificates for HTTPS (needed in scratch image)
RUN apk --no-cache add ca-certificates

WORKDIR /build

# Copy go module files first (layer caching)
COPY go.mod go.sum .

# Download dependencies (if any)
RUN go mod download

# Copy source code
COPY main.go .

# Build static binary
# CGO_ENABLED=0: Pure Go, no C dependencies
# -ldflags="-s -w": Strip debug info for smaller binary
# -o: Output binary name
RUN CGO_ENABLED=0 GOOS=${TARGETOS} GOARCH=${TARGETARCH:-amd64} go build \
    -ldflags="-s -w" \
    -o devops-info-service \
    main.go

# =============================================================================
# Stage 2: Runtime - Minimal production image
# =============================================================================
FROM scratch

# Import CA certificates from builder (for HTTPS if needed)
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

# Copy the binary from builder stage
COPY --from=builder /build/devops-info-service /devops-info-service

# Expose the application port
EXPOSE 8080

# Set default environment variables
ENV HOST=0.0.0.0 \
    PORT=8080

# Run as non-root (UID 1000)
USER 1000:1000

# Run the binary
ENTRYPOINT ["/devops-info-service"]
