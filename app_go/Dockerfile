# Stage 1: Builder
# Use full Go SDK image for compilation
FROM golang:1.24-alpine AS builder

# Set working directory
WORKDIR /build

# Copy go mod files first for better caching
COPY go.mod ./

# Download dependencies
RUN go mod download

# Copy source code
COPY main.go .

# Build static binary
# CGO_ENABLED=0 creates a static binary that doesn't require C libraries
# -ldflags="-s -w" strips debug symbols to reduce binary size
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o devops-service main.go

# Stage 2: Runtime
# Use minimal Alpine image for runtime
FROM alpine:latest

# Install CA certificates for HTTPS (if needed)
RUN apk --no-cache add ca-certificates

# Create non-root user
RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser

# Set working directory
WORKDIR /app

# Copy binary from builder stage
COPY --from=builder /build/devops-service .

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8080

# Set environment variable
ENV PORT=8080

# Run the binary
CMD ["./devops-service"]
