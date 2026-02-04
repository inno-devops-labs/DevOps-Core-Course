###############################################################################
# Stage 1: Builder
# Purpose: Compile the Go application
# Base image: Full Go SDK with build tools
###############################################################################
FROM golang:1.21-alpine AS builder

# Set the working directory inside the container
WORKDIR /build

# Install git and other build dependencies (if needed for go mod download)
RUN apk add --no-cache git ca-certificates

# Copy go mod files first for better layer caching
# This layer will only be rebuilt when dependencies change
COPY go.mod go.sum* ./

# Download dependencies
RUN go mod download

# Copy source code
COPY main.go .

# Build the application
# -ldflags="-s -w" strips debug information to reduce binary size
# -o specifies the output filename
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o devops-info-service .


###############################################################################
# Stage 2: Runtime
# Purpose: Run the application with minimal footprint
# Base image: Alpine Linux (minimal but with basic tools)
###############################################################################
FROM alpine:3.19

# Install ca-certificates for HTTPS and wget for healthcheck
RUN apk add --no-cache ca-certificates wget

# Create non-root user
RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser

# Copy CA certificates from builder
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

# Copy the compiled binary from builder stage
COPY --from=builder /build/devops-info-service /usr/local/bin/devops-info-service

# Set ownership to non-root user
RUN chown appuser:appuser /usr/local/bin/devops-info-service

# Switch to non-root user
USER appuser

# Expose the application port
EXPOSE 8080

# Set default environment variables
ENV HOST=0.0.0.0 \
    PORT=8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

# Run the binary
ENTRYPOINT ["/usr/local/bin/devops-info-service"]
