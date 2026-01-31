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

# Stage 2: Minimal runtime
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