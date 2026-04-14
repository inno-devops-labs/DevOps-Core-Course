# Stage 1: Builder - Full Go environment for compilation
FROM golang:1.23-alpine AS builder

# Install build dependencies
RUN apk add --no-cache git

# Set working directory
WORKDIR /build

# Copy Go module files first for layer caching
COPY go.mod ./

# Copy source code
COPY main.go .

# Build static binary with optimizations
# CGO_ENABLED=0 for static binary (no C dependencies)
# -ldflags to strip debug info and reduce size
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o devops-info-service main.go

# Stage 2: Runtime - Minimal image for deployment
FROM alpine:3.19

# Create non-root user
RUN addgroup -S appuser && adduser -S appuser -G appuser

# Set working directory
WORKDIR /app

# Copy only the compiled binary from builder stage
COPY --from=builder /build/devops-info-service .

# Create data directory for visits persistence
RUN mkdir -p /data

# Change ownership to non-root user
RUN chown -R appuser:appuser /app /data

# Switch to non-root user
USER appuser

# Document port
EXPOSE 8080

# Set default environment variables
ENV HOST=0.0.0.0 \
    PORT=8080

# Run the binary
CMD ["./devops-info-service"]
