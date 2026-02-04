# syntax=docker/dockerfile:1

# Stage 1: Builder
# Use official Golang image for building
FROM golang:1.23-alpine AS builder

# Install build dependencies (git for go modules, ca-certificates for HTTPS)
RUN apk add --no-cache git ca-certificates tzdata

# Set working directory
WORKDIR /build

# Copy go.mod first for better layer caching
COPY go.mod ./

# Download dependencies (cached if go.mod doesn't change)
RUN go mod download

# Copy source code
COPY main.go ./

# Build the application
# CGO_ENABLED=0: Static binary (no C dependencies)
# -ldflags="-w -s": Strip debug info and symbol table (smaller binary)
# -trimpath: Remove file system paths from binary (security + smaller size)
RUN CGO_ENABLED=0 go build \
    -ldflags="-w -s" \
    -trimpath \
    -o /build/app \
    main.go

# Stage 2: Runtime (minimal alpine)
# Use alpine for minimal runtime image (~5MB base)
FROM alpine:3.19

# Install only CA certificates for HTTPS (no other dependencies needed)
RUN apk add --no-cache ca-certificates tzdata && \
    adduser -D -u 1000 -s /sbin/nologin appuser

# Copy the compiled binary from builder stage
COPY --from=builder /build/app /app

# Set working directory
WORKDIR /

# Set environment variables
ENV HOST=0.0.0.0 \
    PORT=8080 \
    TZ=UTC

# Expose the port the app runs on
EXPOSE 8080

# Switch to non-root user
USER appuser

# Health check (alpine has wget)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

# Run the application
ENTRYPOINT ["/app"]
